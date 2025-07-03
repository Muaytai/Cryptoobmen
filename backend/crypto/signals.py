from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=None)  # sender будет указан внутри функции
def create_user_wallets(sender, instance, created, **kwargs):
    from .models import Cryptocurrency, UserWallet
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if sender is User and created:
        active_currencies = Cryptocurrency.objects.filter(is_active=True)
        for currency_obj in active_currencies:
            UserWallet.objects.get_or_create(
                user=instance,
                currency=currency_obj,
                defaults={'balance': 0, 'available_balance': 0, 'is_active': True}
            )

@receiver(post_save, sender=None)
def create_wallets_for_new_cryptocurrency(sender, instance, created, **kwargs):
    from .models import UserWallet, Cryptocurrency
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if sender is Cryptocurrency and created and instance.is_active:
        users = User.objects.all()
        for user in users:
            UserWallet.objects.get_or_create(
                user=user,
                currency=instance,
                defaults={'balance': 0, 'available_balance': 0, 'is_active': True}
            )

@receiver(post_save, sender=None)
def send_deposit_status_update(sender, instance, **kwargs):
    from .models import UserDepositMemo
    if sender is UserDepositMemo:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        try:
            if instance.status in ['used', 'expired']:
                logger.info(f"Caught status change for memo {instance.memo} to '{instance.status}'. Sending WebSocket update.")
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
                    logger.info(f"Successfully sent WebSocket update to group {group_name}")
        except Exception as e:
            logger.error(f"Error in send_deposit_status_update signal for memo {instance.memo}: {e}")

def refund_on_cancel(sender, instance, created, **kwargs):
    logger.warning(f"=== SIGNAL: refund_on_cancel called for sender={sender}, instance.id={getattr(instance, 'id', None)}, status={getattr(instance, 'status', None)}, refunded={getattr(instance, 'refunded', None)}")
    if instance.status == 'cancelled' and not instance.refunded:
        wallet = instance.wallet
        amount = instance.transaction.amount
        logger.warning(f"=== SIGNAL: refund_on_cancel: Попытка возврата {amount} в кошелек {getattr(wallet, 'id', None)}")
        wallet.balance += amount
        wallet.save(update_fields=["balance"])
        instance.refunded = True
        instance.save(update_fields=["refunded"])
        logger.warning(f"=== SIGNAL: refund_on_cancel: Баланс кошелька {wallet.id} теперь {wallet.balance}, Withdrawal.refunded={instance.refunded}")
    else:
        logger.warning(f"=== SIGNAL: refund_on_cancel: Условия не выполнены для возврата (status={instance.status}, refunded={instance.refunded})")

def refund_on_transaction_cancel(sender, instance, created, **kwargs):
    logger.warning(f"=== SIGNAL: refund_on_transaction_cancel called for sender={sender}, instance.id={getattr(instance, 'id', None)}, type={getattr(instance, 'type', None)}, status={getattr(instance, 'status', None)}")
    if instance.type == 'withdrawal' and instance.status == 'cancelled':
        try:
            from transactions.models import Withdrawal
            withdrawal = Withdrawal.objects.filter(transaction=instance).first()
            if not withdrawal:
                logger.error(f"=== SIGNAL: Withdrawal not found for Transaction #{instance.id}")
                return
            if withdrawal.refunded:
                logger.warning(f"=== SIGNAL: Withdrawal already refunded for Transaction #{instance.id}")
                return
            wallet = withdrawal.wallet
            if not wallet:
                logger.error(f"=== SIGNAL: Wallet not found for Withdrawal #{withdrawal.id}")
                return
            amount = instance.amount
            logger.warning(f"=== SIGNAL: refund_on_transaction_cancel: Попытка возврата {amount} в кошелек {wallet.id}")
            wallet.balance += amount
            wallet.save(update_fields=["balance"])
            withdrawal.refunded = True
            withdrawal.save(update_fields=["refunded"])
            logger.warning(f"=== SIGNAL: refund_on_transaction_cancel: Баланс кошелька {wallet.id} теперь {wallet.balance}, Withdrawal.refunded={withdrawal.refunded}")
        except Exception as e:
            logger.error(f"=== SIGNAL: refund_on_transaction_cancel: Ошибка возврата: {e}")
    else:
        logger.warning(f"=== SIGNAL: refund_on_transaction_cancel: Условия не выполнены для возврата (type={instance.type}, status={instance.status})")

# Регистрация сигнала будет происходить в apps.py в методе ready() 
# Регистрация сигнала для Transaction будет происходить в apps.py в методе ready() 