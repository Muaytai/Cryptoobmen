from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model # Keep for reference if UserProfile model needs it explicitly
from .models import UserProfile

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


# --- Удален дублирующий сигнал create_user_wallets --- 
# Он был здесь и вызывал ошибку из-за использования старого поля 'crypto'.
# Функциональность по созданию кошельков для новых пользователей обрабатывается
# сигналами в crypto/signals.py, которые уже исправлены.