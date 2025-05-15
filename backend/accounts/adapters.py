from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.shortcuts import redirect
from urllib.parse import urlparse


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

    def get_login_redirect_url(self, request):
        """Перенаправляет на фронтенд после логина"""
        # Проверяем, есть ли параметр next в запросе
        next_url = request.GET.get('next', None)
        if next_url:
            return next_url
        return settings.FRONTEND_URL + '/profile'
        
    def is_safe_url(self, url):
        """Переопределяем проверку безопасности URL, разрешая все URL"""
        # Разрешаем любой URL для перенаправления
        return True


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
    
    def get_connect_redirect_url(self, request, socialaccount):
        """Перенаправляет после успешного подключения аккаунта соцсети"""
        next_url = request.GET.get('next')
        if next_url:
            return next_url
        return settings.FRONTEND_URL + '/profile'
    
    def get_login_redirect_url(self, request):
        """Перенаправляет на endpoint обработки социальной авторизации с токеном"""
        # Получаем URL для перенаправления из параметра next или используем дефолтный
        next_url = request.GET.get('next', f"{settings.FRONTEND_URL}/profile")
        
        # Формируем полный URL для перенаправления (включая домен)
        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        base_url = f"{scheme}://{host}"
        
        # Перенаправляем на обработчик социальной авторизации
        callback_url = f"{base_url}/api/accounts/social/callback/?next={next_url}"
        
        return callback_url
    
    def is_safe_url(self, url):
        """Переопределяем проверку безопасности URL, разрешая все URL"""
        # Разрешаем любой URL для перенаправления
        return True
        
    def pre_social_login(self, request, sociallogin):
        """Действия перед авторизацией через соцсеть"""
        # Если пользователь уже зарегистрирован с таким email, автоматически соединяем аккаунты
        if sociallogin.is_existing:
            return
            
        # Если пользователь уже аутентифицирован, соединяем аккаунты
        if request.user.is_authenticated:
            sociallogin.connect(request, request.user)
            return
            
        # Проверяем, существует ли пользователь с таким email
        email = sociallogin.account.extra_data.get('email')
        if not email:
            return
            
        # Поиск пользователя по email
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
            # Если пользователь найден, привязываем социальный аккаунт
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            # Пользователь не найден, продолжаем стандартный процесс регистрации
            pass
            
    def is_auto_signup_allowed(self, request, sociallogin):
        """Проверяет, разрешена ли автоматическая регистрация"""
        # Всегда разрешаем автоматическую регистрацию, даже если аккаунт уже существует
        return True 