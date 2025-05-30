from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model # Keep for reference if UserProfile model needs it explicitly
from .models import UserProfile
from crypto.models import Cryptocurrency, UserWallet

# User = get_user_model() # Replaced by settings.AUTH_USER_MODEL in receivers


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Создает профиль пользователя при создании нового пользователя"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """Сохраняет профиль пользователя при обновлении пользователя"""
    # Проверяем наличие профиля, создаем если отсутствует
    if not hasattr(instance, 'profile'):
        UserProfile.objects.create(user=instance)
    else:
        instance.profile.save()


# --- Новый сигнал для создания кошельков ---
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wallets(sender, instance, created, **kwargs):
    """
    Создает кошельки для всех активных криптовалют для нового пользователя.
    """
    if created: # Только если пользователь был создан (а не обновлен)
        try:
            active_cryptocurrencies = Cryptocurrency.objects.filter(is_active=True)
            wallets_created_count = 0
            for crypto in active_cryptocurrencies:
                wallet, wallet_created = UserWallet.objects.get_or_create(
                    user=instance,
                    crypto=crypto,
                    defaults={'balance': 0, 'available_balance': 0}
                )
                if wallet_created:
                    wallets_created_count += 1
            
            username_attr = getattr(instance, 'username', instance.pk) # Get username or pk

            if wallets_created_count > 0:
                print(f"Создано {wallets_created_count} кошельков для нового пользователя: {username_attr}")
            elif not active_cryptocurrencies.exists():
                print(f"Нет активных криптовалют для создания кошельков пользователю {username_attr}.")
            else:
                # This case implies active_cryptos exist, but no wallets were created (e.g., all get_or_create found existing ones)
                print(f"Кошельки для пользователя {username_attr} уже существуют или не были созданы (get_or_create не вернул created=True).")
        except Exception as e:
            print(f"Ошибка при создании кошельков для пользователя {getattr(instance, 'username', instance.pk)}: {e}")