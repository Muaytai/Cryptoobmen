from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Cryptocurrency, UserWallet

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_wallets(sender, instance, created, **kwargs):
    """Создает кошельки для всех активных криптовалют при создании нового пользователя"""
    if created:
        cryptocurrencies = Cryptocurrency.objects.filter(is_active=True)
        for crypto in cryptocurrencies:
            UserWallet.objects.get_or_create(
                user=instance,
                crypto=crypto,
                defaults={'balance': 0, 'is_active': True}
            )


@receiver(post_save, sender=Cryptocurrency)
def create_wallets_for_new_cryptocurrency(sender, instance, created, **kwargs):
    """Создает кошельки для всех пользователей при добавлении новой криптовалюты"""
    if created and instance.is_active:
        users = User.objects.all()
        for user in users:
            UserWallet.objects.get_or_create(
                user=user,
                crypto=instance,
                defaults={'balance': 0, 'is_active': True}
            ) 