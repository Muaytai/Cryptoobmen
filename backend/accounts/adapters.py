from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings


class CustomAccountAdapter(DefaultAccountAdapter):
    """Пользовательский адаптер для обычной регистрации"""
    
    def save_user(self, request, user, form, commit=True):
        """Сохраняет пользователя и создает его профиль"""
        user = super().save_user(request, user, form, commit=False)
        
        # Дополнительная настройка пользователя
        if hasattr(form, 'cleaned_data'):
            if 'phone_number' in form.cleaned_data:
                user.phone_number = form.cleaned_data['phone_number']
        
        if commit:
            user.save()
            # Создаем профиль пользователя
            from accounts.models import UserProfile
            UserProfile.objects.create(user=user)
            
        return user
    
    def confirm_email(self, request, email_address):
        """Устанавливает флаг is_verified в True после подтверждения email"""
        super().confirm_email(request, email_address)
        # Обновляем поле is_verified у пользователя
        user = email_address.user
        user.is_verified = True
        user.save()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Пользовательский адаптер для социальной аутентификации"""
    
    def populate_user(self, request, sociallogin, data):
        """Заполняет данные пользователя из социальной сети"""
        user = super().populate_user(request, sociallogin, data)
        
        if sociallogin.account.provider == 'google':
            user.is_verified = True  # Автоматически верифицируем пользователей из Google
            # Получаем аватар, если есть
            if 'picture' in sociallogin.account.extra_data:
                from django.core.files.base import ContentFile
                from urllib.request import urlopen
                try:
                    avatar_url = sociallogin.account.extra_data['picture']
                    response = urlopen(avatar_url)
                    user.avatar.save(
                        f'google_{sociallogin.account.uid}.jpg',
                        ContentFile(response.read())
                    )
                except Exception as e:
                    # Игнорируем ошибки при загрузке аватара
                    pass
            
        elif sociallogin.account.provider == 'yandex':
            user.is_verified = True  # Верифицируем пользователей из Яндекс
            # Обработка аватара для Яндекс
            if 'default_avatar_id' in sociallogin.account.extra_data:
                # Логика для получения аватара из Яндекс
                pass
        
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """Сохраняет пользователя, авторизованного через соцсеть"""
        user = super().save_user(request, sociallogin, form)
        
        # Создаем профиль пользователя, если его еще нет
        from accounts.models import UserProfile
        UserProfile.objects.get_or_create(user=user)
        
        return user 