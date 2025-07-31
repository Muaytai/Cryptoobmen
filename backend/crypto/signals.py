from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wallets(sender, instance, created, **kwargs):
    """Создает кошельки для нового пользователя"""
    if created:
        from .models import Cryptocurrency, UserWallet
        active_currencies = Cryptocurrency.objects.filter(is_active=True)
        for currency_obj in active_currencies:
            UserWallet.objects.get_or_create(
                user=instance,
                currency=currency_obj,
                defaults={'balance': 0, 'available_balance': 0, 'is_active': True}
            )

@receiver(post_save, sender='crypto.Cryptocurrency')
def create_wallets_for_new_cryptocurrency(sender, instance, created, **kwargs):
    """Создает кошельки для всех пользователей при добавлении новой криптовалюты"""
    if created and instance.is_active:
        from .models import UserWallet
        from django.contrib.auth import get_user_model
        User = get_user_model()
        users = User.objects.all()
        for user in users:
            UserWallet.objects.get_or_create(
                user=user,
                currency=instance,
                defaults={'balance': 0, 'available_balance': 0, 'is_active': True}
            )

@receiver(post_save, sender='crypto.UserDepositMemo')
def send_deposit_status_update(sender, instance, **kwargs):
    """Отправляет WebSocket уведомления об изменении статуса депозита"""
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
    try:
        if instance.status in ['used', 'expired']:
            channel_layer = get_channel_layer()
            group_name = f'deposit_memo_{instance.memo}'
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        "type": "deposit.status.update",
                        "data": {
                            'status': instance.status,
                            'memo': instance.memo,
                        }
                    }
                )
    except Exception as e:
        logger.error(f"Error in send_deposit_status_update signal for memo {instance.memo}: {e}")

from transactions.models import Transaction as TransactionModel, Withdrawal as WithdrawalModel


@receiver(post_save, sender=TransactionModel)
def handle_transaction_status_change(sender, instance, **kwargs):
    """
    Обрабатывает изменение статуса транзакции.
    Возвращает средства пользователю при отмене или ошибке вывода.
    """
    # Проверяем, изменился ли статус на 'cancelled' или 'failed'
    if (instance.status in ['cancelled', 'failed'] and 
        instance.type == 'withdrawal'):
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
        

