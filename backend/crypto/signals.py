from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Используем реальные классы моделей как senders для корректной регистрации сигналов
User = get_user_model()
from .models import Cryptocurrency, UserWallet, UserDepositMemo  # noqa: E402 – импорт после настройки Django

def _create_missing_wallets_for_user(user: User) -> None:  # type: ignore[name-defined]
    """Создает недостающие кошельки для пользователя по всем активным криптовалютам.

    Использует bulk_create для эффективности и исключает возможные дубликаты.
    """
    active_currency_qs = Cryptocurrency.objects.filter(is_active=True, currency_type='crypto')
    existing_currency_ids = set(
        UserWallet.objects.filter(user=user).values_list('currency_id', flat=True)
    )

    wallets_to_create = [
        UserWallet(
            user=user,
            currency=currency_obj,
            balance=0,
            available_balance=0,
            locked_balance=0,
            is_active=True,
        )
        for currency_obj in active_currency_qs
        if currency_obj.id not in existing_currency_ids
    ]

    if wallets_to_create:
        UserWallet.objects.bulk_create(wallets_to_create, ignore_conflicts=True)
        logger.info(
            "Created %s wallets for user %s", len(wallets_to_create), getattr(user, 'email', user.pk)
        )

@receiver(post_save, sender=User, dispatch_uid='crypto_create_user_wallets')
def create_user_wallets(sender, instance, created, **kwargs):
    """Создает кошельки для нового пользователя после коммита транзакции."""
    if not created:
        return

    # Отложим создание кошельков до успешного коммита транзакции, чтобы избежать гонок
    transaction.on_commit(lambda: _create_missing_wallets_for_user(instance))

@receiver(post_save, sender=Cryptocurrency, dispatch_uid='crypto_create_wallets_for_new_currency')
def create_wallets_for_new_cryptocurrency(sender, instance, created, **kwargs):
    """Создает кошельки для всех пользователей при добавлении новой криптовалюты"""
    if not (created and instance.is_active and instance.currency_type == 'crypto'):
        return

    def _create_for_all_users():
        users = User.objects.all()
        existing = set(
            UserWallet.objects.filter(currency=instance).values_list('user_id', flat=True)
        )
        to_create = [
            UserWallet(
                user=user,
                currency=instance,
                balance=0,
                available_balance=0,
                locked_balance=0,
                is_active=True,
            )
            for user in users
            if user.id not in existing
        ]
        if to_create:
            UserWallet.objects.bulk_create(to_create, ignore_conflicts=True)
            logger.info("Created %s wallets for new currency %s", len(to_create), instance)

    transaction.on_commit(_create_for_all_users)

# ВРЕМЕННО ОТКЛЮЧЕНО для отладки
# @receiver(post_save, sender=UserDepositMemo)
def send_deposit_status_update_DISABLED(sender, instance, **kwargs):
    """Отправляет WebSocket уведомления об изменении статуса депозита - ОТКЛЮЧЕНО"""
    logger.info(f"DISABLED: Would send WebSocket update for memo {instance.memo} status {instance.status}")
    # from asgiref.sync import async_to_sync
    # from channels.layers import get_channel_layer
    # try:
    #     if instance.status in ['used', 'expired']:
    #         logger.info(f"Caught status change for memo {instance.memo} to '{instance.status}'. Sending WebSocket update.")
    #         channel_layer = get_channel_layer()
    #         group_name = f'deposit_memo_{instance.memo}'
    #         if channel_layer:
    #             async_to_sync(channel_layer.group_send)(
    #                 group_name,
    #                 {
    #                     "type": "deposit.status.update",
    #                     "data": {
    #                         'status': instance.status,
    #                         'memo': instance.memo,
    #                     }
    #                 }
    #             )
    #             logger.info(f"Successfully sent WebSocket update to group {group_name}")
    # except Exception as e:
    #     logger.error(f"Error in send_deposit_status_update signal for memo {instance.memo}: {e}")

from transactions.models import Transaction as TransactionModel, Withdrawal as WithdrawalModel

@receiver(post_save, sender=TransactionModel)
def handle_transaction_status_change(sender, instance, **kwargs):
    """
    Обрабатывает изменение статуса транзакции.
    Возвращает средства пользователю при отмене или ошибке вывода.
    """
    logger.info(f"Signal handle_transaction_status_change called for transaction {instance.pk}")
    
    if instance.type != 'withdrawal':
        return

    # Возврат средств только при отмене/ошибке вывода
    if instance.status in ['cancelled', 'failed']:
        
        logger.info(f"Refunding transaction {instance.pk}")
        # Ищем связанный объект Withdrawal
        try:
            from transactions.models import Withdrawal
            withdrawal = Withdrawal.objects.get(transaction=instance)
            
            # Проверяем, что средства еще не были возвращены
            if not withdrawal.refunded and withdrawal.wallet:
                # ⚠️ ВАЖНО: При возврате средств нужно:
                # 1. Вернуть средства на баланс пользователя
                # 2. Разблокировать замороженные средства (locked_balance)
                # 3. Вернуть available_balance
                
                # Рассчитываем сумму для возврата (включая комиссию и газ)
                # Используем ту же логику, что и при блокировке
                from .gas_calculation import calculate_withdrawal_gas_cost
                
                try:
                    # ⚠️ ВАЖНО: instance.amount - это сумма после вычета fee (amount_after_fee)
                    # Но для расчета total_cost нужно использовать сумму ДО вычета fee
                    # Поэтому используем instance.amount + instance.fee как withdrawal_amount
                    # Или можно просто сложить: amount + fee + gas
                    
                    # Рассчитываем газ для суммы после fee (как в process_withdrawal)
                    gas_cost = calculate_withdrawal_gas_cost(
                        currency=instance.crypto,
                        withdrawal_amount=instance.amount,
                        destination_address=withdrawal.destination_address
                    )
                    
                    # Общая заблокированная сумма = amount + fee + gas
                    total_locked_amount = instance.amount + instance.fee + gas_cost
                    
                    # ⚠️ КРИТИЧЕСКИ ВАЖНО: При возврате средств нужно вернуть ВСЮ заблокированную сумму,
                    # а не только instance.amount! При блокировке было списано total_amount с balance,
                    # поэтому нужно вернуть total_amount обратно на balance.
                    # amount - это сумма после fee, но на баланс была списана total_amount (amount + fee + gas)
                    withdrawal.wallet.balance += total_locked_amount
                    withdrawal.wallet.available_balance += total_locked_amount
                    
                    # ⚠️ КРИТИЧЕСКИ ВАЖНО: Разблокируем замороженные средства
                    # Используем max() чтобы избежать отрицательного locked_balance
                    withdrawal.wallet.locked_balance = max(
                        Decimal('0'),
                        withdrawal.wallet.locked_balance - total_locked_amount
                    )
                    
                    withdrawal.wallet.save(update_fields=['balance', 'available_balance', 'locked_balance'])
                    
                    logger.info(
                        f"Возвращены средства пользователю {instance.user.email}: "
                        f"{total_locked_amount} {instance.crypto.symbol} "
                        f"(amount: {instance.amount}, fee: {instance.fee}, gas: {gas_cost}, транзакция {instance.transaction_id}). "
                        f"Разблокировано: {total_locked_amount} {instance.crypto.symbol}"
                    )
                except Exception as calc_error:
                    # Если не удалось рассчитать точную сумму, используем упрощенный подход
                    logger.warning(f"Не удалось рассчитать точную заблокированную сумму для возврата: {calc_error}. Используем упрощенный подход.")
                    
                    # Упрощенный подход: используем amount + fee (без газа, так как газ может измениться)
                    # Это консервативный подход - вернем меньше, чем заблокировано, но не потеряем средства пользователя
                    simplified_total = instance.amount + instance.fee
                    
                    withdrawal.wallet.balance += simplified_total
                    withdrawal.wallet.available_balance += simplified_total
                    
                    # Разблокируем сумму, равную simplified_total (консервативный подход)
                    withdrawal.wallet.locked_balance = max(
                        Decimal('0'),
                        withdrawal.wallet.locked_balance - simplified_total
                    )
                    withdrawal.wallet.save(update_fields=['balance', 'available_balance', 'locked_balance'])
                    
                    logger.warning(
                        f"Возвращены средства пользователю {instance.user.email}: "
                        f"{simplified_total} {instance.crypto.symbol} "
                        f"(amount: {instance.amount}, fee: {instance.fee}, gas не учтен, транзакция {instance.transaction_id}, упрощенный расчет). "
                        f"⚠️ Может потребоваться ручная разблокировка оставшихся средств."
                    )
                
                # Отмечаем, что средства возвращены
                withdrawal.refunded = True
                withdrawal.save(update_fields=['refunded'])
                
        except Withdrawal.DoesNotExist:
            logger.warning(
                f"Не найден объект Withdrawal для транзакции {instance.transaction_id}"
            )
        except Exception as e:
            logger.error(
                f"Ошибка при возврате средств для транзакции {instance.transaction_id}: {e}"
            )

@receiver(post_save, sender=WithdrawalModel)
def handle_withdrawal_status_change(sender, instance, **kwargs):
    """
    Дополнительный сигнал для обработки изменений в модели Withdrawal
    ⚠️ ВАЖНО: Возвращает полную сумму (amount + fee + gas_cost), если средства были заблокированы
    """
    if hasattr(instance, '_state') and instance._state.adding:
        # Это новый объект, ничего не делаем
        return
        
    # Проверяем статус связанной транзакции
    # ⚠️ ВАЖНО: Проверяем refunded и locked_balance, чтобы избежать двойного возврата
    if (instance.transaction.status in ['cancelled', 'failed'] and 
        not instance.refunded and 
        instance.wallet):
        
        with transaction.atomic():
            # Блокируем кошелек для обновления
            wallet = UserWallet.objects.select_for_update().get(id=instance.wallet.id)
            
            # ⚠️ ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: Если нет заблокированных средств, значит уже возвращены
            if wallet.locked_balance <= 0:
                logger.info(
                    f"Skipping refund for withdrawal {instance.id}: "
                    f"no locked balance (already refunded or never locked)"
                )
                # Отмечаем как возвращенные, чтобы не проверять снова
                instance.refunded = True
                instance.save(update_fields=['refunded'])
                return
            
            # ⚠️ ВАЖНО: Рассчитываем полную сумму для возврата (включая gas_cost)
            # Это должно совпадать с total_amount, который был списан в process_withdrawal
            from .gas_calculation import calculate_withdrawal_gas_cost
            amount_to_send = instance.transaction.amount
            platform_fee = instance.transaction.fee
            gas_cost = calculate_withdrawal_gas_cost(
                currency=instance.transaction.crypto,
                withdrawal_amount=amount_to_send,
                destination_address=instance.destination_address
            )
            total_amount_to_refund = amount_to_send + platform_fee + gas_cost
            
            # Проверяем, что есть заблокированные средства для возврата
            # Если locked_balance >= total_amount, возвращаем полную сумму
            # Если locked_balance < total_amount, возвращаем то, что есть
            if wallet.locked_balance >= total_amount_to_refund:
                wallet.locked_balance -= total_amount_to_refund
                wallet.balance += total_amount_to_refund
                refunded_amount = total_amount_to_refund
            elif wallet.locked_balance > 0:
                # Частичный возврат
                refunded_amount = wallet.locked_balance
                wallet.balance += refunded_amount
                wallet.locked_balance = Decimal('0')
            else:
                # Нет заблокированных средств, возможно уже возвращены
                logger.warning(
                    f"No locked balance to refund for withdrawal {instance.id}. "
                    f"Locked: {wallet.locked_balance}, Required: {total_amount_to_refund}"
                )
                refunded_amount = Decimal('0')
            
            wallet.save(update_fields=['balance', 'locked_balance'])
            
            # Отмечаем, что средства возвращены
            instance.refunded = True
            instance.save(update_fields=['refunded'])
            
            if refunded_amount > 0:
                logger.info(
                    f"Возвращены средства пользователю {instance.user.email}: "
                    f"{refunded_amount} {instance.transaction.crypto.symbol} "
                    f"(amount: {amount_to_send}, fee: {platform_fee}, gas: {gas_cost}, withdrawal {instance.id})"
                )
