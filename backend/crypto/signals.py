from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
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
    
    # Проверяем, изменился ли статус на 'cancelled' или 'failed'
    if (instance.status in ['cancelled', 'failed'] and 
        instance.type == 'withdrawal'):
        
        logger.info(f"Refunding transaction {instance.pk}")
        # Ищем связанный объект Withdrawal
        try:
            from transactions.models import Withdrawal
            withdrawal = Withdrawal.objects.get(transaction=instance)
            
            # Проверяем, что средства еще не были возвращены
            if not withdrawal.refunded and withdrawal.wallet:
                # Возвращаем средства на баланс пользователя
                withdrawal.wallet.balance += instance.amount
                withdrawal.wallet.available_balance += instance.amount
                withdrawal.wallet.save(update_fields=['balance', 'available_balance'])
                
                # Отмечаем, что средства возвращены
                withdrawal.refunded = True
                withdrawal.save(update_fields=['refunded'])
                
                logger.info(
                    f"Возвращены средства пользователю {instance.user.email}: "
                    f"{instance.amount} {instance.crypto.symbol} "
                    f"(транзакция {instance.transaction_id})"
                )
                
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
    """
    if hasattr(instance, '_state') and instance._state.adding:
        # Это новый объект, ничего не делаем
        return
        
    # Проверяем статус связанной транзакции
    if (instance.transaction.status in ['cancelled', 'failed'] and 
        not instance.refunded and 
        instance.wallet):
        
        # Возвращаем средства на баланс пользователя
        instance.wallet.balance += instance.transaction.amount
        instance.wallet.available_balance += instance.transaction.amount
        instance.wallet.save(update_fields=['balance', 'available_balance'])
        
        # Отмечаем, что средства возвращены
        instance.refunded = True
        instance.save(update_fields=['refunded'])
        
        logger.info(
            f"Возвращены средства пользователю {instance.user.email}: "
            f"{instance.transaction.amount} {instance.transaction.crypto.symbol} "
            f"(вывод {instance.id})"
        )
