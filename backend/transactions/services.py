import uuid
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from django.db import transaction as db_transaction
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers # Для вызова ValidationError

from .models import Transaction, Withdrawal, Transfer
from crypto.models import Cryptocurrency, UserWallet
from crypto.tasks import process_withdrawal
from accounts.models import User

from crypto.services import get_exchange_rates
from crypto.models import ExchangePair
from transactions.models import Exchange as TransactionExchange


class ExchangeService:
    """Сервис, инкапсулирующий бизнес-логику обмена валют."""

    @staticmethod
    def _get_usd_rate(crypto, live_rates: dict) -> Decimal:
        """Возвращает курс валюты к USD в Decimal."""
        if crypto.symbol.upper() == 'USD':
            return Decimal('1')
        if not crypto.coingecko_id or crypto.coingecko_id not in live_rates:
            raise serializers.ValidationError(f"Курс для {crypto.symbol} не найден у провайдера.")
        usd_value = live_rates[crypto.coingecko_id].get('usd')
        if usd_value is None:
            raise serializers.ValidationError(f"В ответе провайдера нет USD цены для {crypto.symbol}.")
        return Decimal(str(usd_value))

    @staticmethod
    def calculate_by_currencies(from_crypto, to_crypto, amount: Decimal):
        """Рассчитать обмен без привязки к кошелькам (публичный калькулятор)."""
        # Проверяем пару
        pair = ExchangePair.objects.filter(from_crypto=from_crypto, to_crypto=to_crypto, is_active=True).first()
        if not pair:
            raise serializers.ValidationError("Пара обмена неактивна или не существует.")

        # Проверяем лимиты
        min_amount = pair.min_from_amount or from_crypto.min_exchange_amount
        max_amount = pair.max_from_amount or from_crypto.max_exchange_amount
        if amount < min_amount:
            raise serializers.ValidationError(f"Минимальная сумма: {min_amount} {from_crypto.symbol}")
        if max_amount and amount > max_amount:
            raise serializers.ValidationError(f"Максимальная сумма: {max_amount} {from_crypto.symbol}")

        # Получаем курсы
        live_rates = get_exchange_rates()
        if live_rates is None:
            raise serializers.ValidationError("Провайдер курсов недоступен. Попробуйте позже.")

        from_usd = ExchangeService._get_usd_rate(from_crypto, live_rates)
        to_usd = ExchangeService._get_usd_rate(to_crypto, live_rates)
        rate = from_usd / to_usd

        # Комиссия
        fee_percent = pair.custom_fee_percentage if pair.custom_fee_percentage is not None else from_crypto.fee_percentage
        fee_amount = (amount * fee_percent) / Decimal('100')
        amount_after_fee = amount - fee_amount
        to_amount = amount_after_fee * rate

        return {
            'rate': rate,
            'fee_percent': fee_percent,
            'fee_amount': fee_amount,
            'to_amount': to_amount
        }

    @staticmethod
    def calculate(from_wallet: 'UserWallet', to_wallet: 'UserWallet', amount: Decimal):
        """Рассчитать обмен между кошельками конкретного пользователя."""
        if from_wallet.user != to_wallet.user:
            raise serializers.ValidationError("Кошельки принадлежат разным пользователям.")
        if amount <= 0:
            raise serializers.ValidationError("Сумма должна быть положительной.")
        if from_wallet.balance < amount:
            raise serializers.ValidationError("Недостаточно средств на балансе.")

        return ExchangeService.calculate_by_currencies(from_wallet.currency, to_wallet.currency, amount)

    @staticmethod
    @db_transaction.atomic
    def perform(user, from_wallet: 'UserWallet', to_wallet: 'UserWallet', amount: Decimal):
        """Выполнить обмен: списать средства, зачислить на другой кошелек и создать записи транзакций."""
        if user != from_wallet.user or user != to_wallet.user:
            raise serializers.ValidationError("Кошельки не принадлежат пользователю.")

        calc = ExchangeService.calculate(from_wallet, to_wallet, amount)

        # Блокируем кошельки для безопасной записи
        from_wallet = UserWallet.objects.select_for_update().get(id=from_wallet.id)
        to_wallet = UserWallet.objects.select_for_update().get(id=to_wallet.id)

        if from_wallet.balance < amount:
            raise serializers.ValidationError("Баланс изменился. Недостаточно средств.")

        # Списываем и начисляем
        from_wallet.balance -= amount
        to_wallet.balance += calc['to_amount']
        from_wallet.save()
        to_wallet.save()

        # Создаем общую транзакцию и Exchange
        tx = Transaction.objects.create(
            user=user,
            type='exchange',
            status='completed',
            amount=amount,
            fee=calc['fee_amount'],
            crypto=from_wallet.currency
        )
        TransactionExchange.objects.create(
            user=user,
            transaction=tx,
            from_crypto=from_wallet.currency,
            to_crypto=to_wallet.currency,
            from_amount=amount,
            to_amount=calc['to_amount'],
            rate=calc['rate'],
            fee_percentage=calc['fee_percent'],
            fee_amount=calc['fee_amount']
        )

        return tx


class WithdrawalService:
    """
    Сервис для управления процессом вывода средств с подтверждением.
    """

    @staticmethod
    def create_withdrawal_request(
        user: User,
        crypto_id: int,
        amount: Decimal,
        destination_address: str,
        memo: str = None,
        ip_address: str = None
    ):
        """
        Создает запрос на вывод и отправляет email для подтверждения.
        Средства не списываются до подтверждения.
        """
        # --- Блок валидации (взят и адаптирован из старого сериализатора) ---
        try:
            crypto = Cryptocurrency.objects.get(id=crypto_id, is_active=True)
            wallet = UserWallet.objects.get(user=user, currency=crypto, is_active=True)
            
            # Проверяем баланс
            if wallet.balance < amount:
                raise serializers.ValidationError(f"Недостаточно средств. Баланс: {wallet.balance} {crypto.symbol}")
            
            # Проверяем минимальную сумму
            if amount < crypto.min_exchange_amount:
                raise serializers.ValidationError(f"Минимальная сумма вывода: {crypto.min_exchange_amount} {crypto.symbol}")
            
            # Рассчитываем комиссию
            fee_percentage = crypto.fee_percentage
            fee_amount = (amount * fee_percentage) / 100
            amount_after_fee = amount - fee_amount
            if amount_after_fee <= 0:
                raise serializers.ValidationError("Сумма к выводу после комиссии должна быть положительной")

            # Проверяем MEMO
            if getattr(crypto, 'requires_memo', False) and not memo:
                raise serializers.ValidationError("Для этой валюты требуется MEMO/Tag")

        except Cryptocurrency.DoesNotExist:
            raise serializers.ValidationError("Криптовалюта не найдена или неактивна")
        except UserWallet.DoesNotExist:
            raise serializers.ValidationError("Кошелек не найден")
        # --- Конец блока валидации ---

        with db_transaction.atomic():
            # Создаем транзакцию со статусом "ожидает подтверждения"
            transaction_obj = Transaction.objects.create(
                user=user,
                type='withdrawal',
                status='awaiting_confirmation',
                amount=amount_after_fee,
                fee=fee_amount,
                crypto=crypto,
                ip_address=ip_address,
                notes=f"Withdrawal request for {amount} {crypto.symbol} to {destination_address} (net: {amount_after_fee})"
            )

            # Генерируем токен и время его жизни
            token = uuid.uuid4()
            expires_at = timezone.now() + timedelta(hours=settings.WITHDRAWAL_CONFIRMATION_TOKEN_LIFETIME_HOURS)

            # Создаем объект вывода
            withdrawal_obj = Withdrawal.objects.create(
                user=user,
                transaction=transaction_obj,
                wallet=wallet,
                destination_address=destination_address,
                memo=memo,
                is_email_confirmed=False,
                email_confirmation_token=token,
                email_confirmation_token_expires_at=expires_at
            )

        # Отправляем письмо для подтверждения (вне атомарной транзакции)
        WithdrawalService.send_confirmation_email(user, withdrawal_obj)

        return withdrawal_obj

    @staticmethod
    def send_confirmation_email(user: User, withdrawal: Withdrawal):
        """
        Отправляет email с ссылкой для подтверждения вывода.
        """
        """
        Отправляет email с ссылкой для подтверждения вывода.
        """
        confirmation_url = f"{settings.FRONTEND_URL}/confirm-withdrawal/{withdrawal.email_confirmation_token}/"
        
        context = {
            'user': user,
            'withdrawal': withdrawal,
            'confirmation_url': confirmation_url,
            'amount': withdrawal.transaction.amount,
            'currency': withdrawal.transaction.crypto.symbol,
            'address': withdrawal.destination_address,
        }
        
        subject = _("Подтверждение вывода средств")
        
        html_message = render_to_string('emails/withdrawal_confirmation.html', context)
        plain_message = render_to_string('emails/withdrawal_confirmation.txt', context)

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message
        )

    @staticmethod
    def confirm_withdrawal(token: uuid.UUID):
        """
        Подтверждает вывод по токену из email.
        Списывает средства и ставит задачу на отправку.
        """
        try:
            withdrawal = Withdrawal.objects.select_related('transaction', 'user', 'wallet').get(email_confirmation_token=token)
        except Withdrawal.DoesNotExist:
            raise serializers.ValidationError("Запрос на вывод не найден или уже был использован.")

        if withdrawal.is_email_confirmed:
            raise serializers.ValidationError("Этот вывод уже был подтвержден.")

        if timezone.now() > withdrawal.email_confirmation_token_expires_at:
            withdrawal.transaction.status = 'failed'
            withdrawal.transaction.notes = "Confirmation token expired."
            withdrawal.transaction.save()
            raise serializers.ValidationError("Срок действия ссылки для подтверждения истек.")

        with db_transaction.atomic():
            # Обновляем статус вывода и транзакции
            withdrawal.is_email_confirmed = True
            withdrawal.save(update_fields=['is_email_confirmed'])

            withdrawal.transaction.status = 'pending' # Готов к обработке таском
            withdrawal.transaction.save(update_fields=['status'])

            # Ставим задачу на обработку вывода ПОСЛЕ коммита транзакции,
            # чтобы избежать состояния гонки, когда воркер пытается получить
            # еще не сохраненный в БД объект.
            db_transaction.on_commit(
                lambda: process_withdrawal.delay(withdrawal.id)
            )
        
        return withdrawal
