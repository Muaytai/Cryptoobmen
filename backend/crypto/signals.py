from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Cryptocurrency, UserWallet, UserDepositMemo
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging

User = get_user_model()

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_wallets(sender, instance, created, **kwargs):
    """Создает кошельки для всех активных криптовалют при создании нового пользователя"""
    if created:
        active_currencies = Cryptocurrency.objects.filter(is_active=True)
        for currency_obj in active_currencies:
            UserWallet.objects.get_or_create(
                user=instance,
                currency=currency_obj,
                defaults={'balance': 0, 'available_balance': 0, 'is_active': True}
            )


@receiver(post_save, sender=Cryptocurrency)
def create_wallets_for_new_cryptocurrency(sender, instance, created, **kwargs):
    """Создает кошельки для всех пользователей при добавлении новой активной криптовалюты"""
    if created and instance.is_active:
        users = User.objects.all()
        for user in users:
            UserWallet.objects.get_or_create(
                user=user,
                currency=instance,
                defaults={'balance': 0, 'available_balance': 0, 'is_active': True}
            )


@receiver(post_save, sender=UserDepositMemo)
def send_deposit_status_update(sender, instance, **kwargs):
    """
    Отправляет WebSocket-уведомление при изменении статуса депозита.
    """
    try:
        # Мы отправляем и на 'used', и на 'expired', чтобы фронтенд мог обработать оба состояния
        if instance.status in ['used', 'expired']:
            logger.info(f"Caught status change for memo {instance.memo} to '{instance.status}'. Sending WebSocket update.")
            channel_layer = get_channel_layer()
            group_name = f'deposit_memo_{instance.memo}'
            
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        "type": "deposit.status.update",  # Новый, более специфичный тип
                        "data": {
                            'status': instance.status,
                            'memo': instance.memo,
                        }
                    }
                )
                logger.info(f"Successfully sent WebSocket update to group {group_name}")
    except Exception as e:
        logger.error(f"Error in send_deposit_status_update signal for memo {instance.memo}: {e}") 