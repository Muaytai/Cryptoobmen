from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Cryptocurrency, UserWallet, CardDeposit, SystemWallet
from transactions.models import Transaction
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import uuid
import logging

logger = logging.getLogger(__name__)

class CardDepositView(APIView):
    """
    API для пополнения кошелька с банковской карты
    """
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        """
        Создает запрос на пополнение кошелька с банковской карты
        
        Параметры:
        - amount: сумма пополнения
        - currency: валюта пополнения (RUB, USD, EUR)
        - card_number: номер карты (маскируется при сохранении)
        - card_expiry: срок действия карты (MM/YY)
        - card_cvv: CVV-код карты (не сохраняется)
        - crypto_symbol: символ криптовалюты, которую хотим получить
        """
        try:
            # Получаем данные из запроса
            amount = request.data.get('amount')
            currency = request.data.get('currency', 'RUB')
            card_number = request.data.get('card_number')
            card_expiry = request.data.get('card_expiry')
            card_cvv = request.data.get('card_cvv')  # Не сохраняем в базе
            crypto_symbol = request.data.get('crypto_symbol')
            
            # Валидация входных данных
            if not all([amount, card_number, card_expiry, card_cvv, crypto_symbol]):
                return Response({
                    'error': 'Не все обязательные поля заполнены',
                    'required_fields': ['amount', 'card_number', 'card_expiry', 'card_cvv', 'crypto_symbol']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                amount = Decimal(amount)
                if amount <= 0:
                    return Response({'error': 'Сумма должна быть положительной'}, status=status.HTTP_400_BAD_REQUEST)
            except:
                return Response({'error': 'Некорректная сумма'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Проверяем, что валюта является системной
            try:
                system_currency = Cryptocurrency.objects.get(symbol=currency, is_system=True, is_active=True)
            except Cryptocurrency.DoesNotExist:
                return Response({'error': f'Валюта {currency} не поддерживается для пополнения'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Проверяем, что криптовалюта существует
            try:
                crypto = Cryptocurrency.objects.get(symbol=crypto_symbol, is_active=True)
            except Cryptocurrency.DoesNotExist:
                return Response({'error': f'Криптовалюта {crypto_symbol} не найдена или неактивна'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Получаем или создаем кошелек пользователя для выбранной криптовалюты
            user_wallet, created = UserWallet.objects.get_or_create(
                user=request.user,
                crypto=crypto,
                defaults={
                    'balance': 0,
                    'available_balance': 0,
                    'address': f'virtual-{crypto.symbol.lower()}-{request.user.id}'
                }
            )
            
            # Получаем системный кошелек для валюты пополнения
            try:
                system_wallet = SystemWallet.objects.get(crypto=system_currency)
            except SystemWallet.DoesNotExist:
                return Response({'error': 'Системный кошелек не настроен'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Маскируем номер карты для хранения в базе
            card_last4 = card_number[-4:] if len(card_number) >= 4 else card_number
            card_brand = self._detect_card_brand(card_number)
            
            # Рассчитываем комиссию (в процентах от суммы)
            fee_percentage = Decimal('2.0')  # 2% комиссия за пополнение с карты
            fee_amount = (amount * fee_percentage) / Decimal('100.0')
            
            # Получаем курс обмена (в реальном проекте здесь будет запрос к API)
            exchange_rate = self._get_exchange_rate(system_currency.symbol, crypto.symbol)
            
            # Рассчитываем сумму в криптовалюте
            crypto_amount = (amount - fee_amount) / exchange_rate
            
            # Создаем запись о пополнении
            deposit = CardDeposit.objects.create(
                user=request.user,
                wallet=user_wallet,
                amount=amount,
                currency=currency,
                card_last4=card_last4,
                card_brand=card_brand,
                status='processing',  # В реальном проекте здесь будет 'pending' до подтверждения платежа
                fee=fee_amount,
                crypto_amount=crypto_amount,
                exchange_rate=exchange_rate,
                payment_id=str(uuid.uuid4())
            )
            
            # В реальном проекте здесь будет интеграция с платежной системой
            # Для демонстрации сразу подтверждаем платеж
            self._process_deposit(deposit)
            
            return Response({
                'success': True,
                'deposit_id': deposit.deposit_id,
                'amount': float(amount),
                'currency': currency,
                'crypto_amount': float(crypto_amount),
                'crypto_symbol': crypto.symbol,
                'fee': float(fee_amount),
                'exchange_rate': float(exchange_rate),
                'status': deposit.status
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Ошибка при пополнении с карты: {e}", exc_info=True)
            return Response({'error': 'Произошла ошибка при обработке запроса'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _detect_card_brand(self, card_number):
        """Определяет платежную систему карты по номеру"""
        if not card_number:
            return None
            
        card_number = card_number.replace(' ', '')
        
        if card_number.startswith('4'):
            return 'Visa'
        elif card_number.startswith(('51', '52', '53', '54', '55')):
            return 'MasterCard'
        elif card_number.startswith(('34', '37')):
            return 'American Express'
        elif card_number.startswith('62'):
            return 'UnionPay'
        elif card_number.startswith('2'):
            return 'Mir'
        else:
            return 'Unknown'
    
    def _get_exchange_rate(self, from_currency, to_currency):
        """
        Получает курс обмена между валютами
        В реальном проекте здесь будет запрос к API для получения актуального курса
        """
        # Упрощенные курсы для демонстрации
        rates = {
            'RUB_BTC': Decimal('0.0000005'),  # 1 RUB = 0.0000005 BTC
            'RUB_ETH': Decimal('0.000008'),   # 1 RUB = 0.000008 ETH
            'RUB_USDT': Decimal('0.01'),      # 1 RUB = 0.01 USDT
            
            'USD_BTC': Decimal('0.00003'),    # 1 USD = 0.00003 BTC
            'USD_ETH': Decimal('0.0005'),     # 1 USD = 0.0005 ETH
            'USD_USDT': Decimal('1.0'),       # 1 USD = 1 USDT
            
            'EUR_BTC': Decimal('0.000035'),   # 1 EUR = 0.000035 BTC
            'EUR_ETH': Decimal('0.00055'),    # 1 EUR = 0.00055 ETH
            'EUR_USDT': Decimal('1.1'),       # 1 EUR = 1.1 USDT
        }
        
        rate_key = f"{from_currency}_{to_currency}"
        return rates.get(rate_key, Decimal('1.0'))
    
    @transaction.atomic
    def _process_deposit(self, deposit):
        """
        Обрабатывает подтвержденный платеж
        В реальном проекте эта функция будет вызываться после подтверждения от платежной системы
        """
        try:
            # Проверяем, что депозит в статусе processing
            if deposit.status != 'processing':
                return
            
            # Создаем транзакцию
            transaction = Transaction.objects.create(
                user=deposit.user,
                transaction_id=uuid.uuid4(),
                type='deposit',
                status='completed',
                amount=deposit.crypto_amount,
                fee=0,  # Комиссия уже учтена в crypto_amount
                crypto=deposit.wallet.crypto,
                notes=f"Пополнение с карты *{deposit.card_last4}, {deposit.amount} {deposit.currency}"
            )
            
            # Обновляем баланс кошелька
            deposit.wallet.available_balance += deposit.crypto_amount
            deposit.wallet.save()
            
            # Обновляем статус депозита
            deposit.status = 'completed'
            deposit.completed_at = timezone.now()
            deposit.save()
            
            # Логируем успешное пополнение
            logger.info(f"Успешное пополнение: {deposit.user.username}, {deposit.amount} {deposit.currency} -> {deposit.crypto_amount} {deposit.wallet.crypto.symbol}")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке депозита {deposit.deposit_id}: {e}", exc_info=True)
            deposit.status = 'failed'
            deposit.save()
            raise
