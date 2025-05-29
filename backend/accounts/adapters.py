from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import redirect
from urllib.parse import urlparse
from allauth.account.utils import user_email
from allauth.socialaccount.models import SocialLogin
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
import uuid

User = get_user_model()

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

    def get_email_confirmation_url(self, request, emailconfirmation):
        """Возвращает URL для подтверждения email на фронтенде"""
        # Сначала получаем ключ подтверждения
        key = emailconfirmation.key
        
        # Получаем email-адрес и пользователя
        email_address = emailconfirmation.email_address
        user = email_address.user
        
        # Подтверждаем email сразу
        email_address.verified = True
        email_address.set_as_primary(conditional=True)
        email_address.save()
        
        # Устанавливаем флаг is_verified для пользователя
        user.is_verified = True
        user.save()
        
        # Возвращаем URL фронтенда с параметром verified=true
        return f"{settings.FRONTEND_URL}/verify-email?verified=true"
    
    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """Отправляет письмо с подтверждением"""
        current_site = get_current_site(request)
        activate_url = self.get_email_confirmation_url(request, emailconfirmation)
        ctx = {
            "user": emailconfirmation.email_address.user,
            "activate_url": activate_url,
            "current_site": current_site,
            "key": emailconfirmation.key,
        }
        if signup:
            email_template = "account/email/email_confirmation_signup"
        else:
            email_template = "account/email/email_confirmation"
        self.send_mail(email_template, emailconfirmation.email_address.email, ctx)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Пользовательский адаптер для социальной аутентификации"""
    
    def pre_social_login(self, request, sociallogin):
        """Обработка перед социальной авторизацией"""
        email = sociallogin.account.extra_data.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                if not sociallogin.is_existing:
                    # Привязываем существующего пользователя к соцаккаунту
                    sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass

    def populate_user(self, request, sociallogin, data):
        """Заполняет данные пользователя из социальной сети"""
        user = super().populate_user(request, sociallogin, data)
        
        # Автоматически верифицируем пользователей из соцсетей
        user.is_verified = True
        
        # Получаем данные из соцсети
        extra_data = sociallogin.account.extra_data
        
        # Устанавливаем username до сохранения пользователя
        email = extra_data.get('email')
        if email:
            base_username = email.split('@')[0]
            # Если base_username пустой, используем часть email до @
            if not base_username:
                base_username = 'user'
            username = base_username
            counter = 1
            # Проверяем существование username и добавляем число если занят
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            user.username = username
        else:
            # Если email не предоставлен, генерируем уникальный username
            user.username = f"user_{str(uuid.uuid4())[:8]}"
        
        # Заполняем дополнительные поля в зависимости от провайдера
        if sociallogin.account.provider == 'google':
            if 'picture' in extra_data:
                try:
                    from django.core.files.base import ContentFile
                    from urllib.request import urlopen
                    avatar_url = extra_data['picture']
                    response = urlopen(avatar_url)
                    user.avatar.save(
                        f'google_{sociallogin.account.uid}.jpg',
                        ContentFile(response.read()),
                        save=False
                    )
                except Exception as e:
                    print(f"Error saving avatar: {str(e)}")
                    
            if 'name' in extra_data:
                user.full_name = extra_data['name']
            if 'given_name' in extra_data:
                user.first_name = extra_data['given_name']
            if 'family_name' in extra_data:
                user.last_name = extra_data['family_name']
            
        elif sociallogin.account.provider == 'yandex':
            if 'real_name' in extra_data:
                user.full_name = extra_data['real_name']
            if 'first_name' in extra_data:
                user.first_name = extra_data['first_name']
            if 'last_name' in extra_data:
                user.last_name = extra_data['last_name']
        
        return user

    def save_user(self, request, sociallogin, form=None):
        """Сохраняет пользователя, авторизованного через соцсеть"""
        user = super().save_user(request, sociallogin, form)
        
        # Создаем профиль пользователя, если его еще нет
        from accounts.models import UserProfile
        UserProfile.objects.get_or_create(user=user)
        
        # Генерируем JWT токены
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Сохраняем токены в сессии
        request.session['access_token'] = access_token
        request.session['refresh_token'] = refresh_token
        
        return user
    
    def get_connect_redirect_url(self, request, socialaccount):
        """Перенаправляет после успешного подключения аккаунта соцсети"""
        next_url = request.GET.get('next')
        if next_url:
            return next_url
        return settings.FRONTEND_URL
    
    def get_login_redirect_url(self, request):
        """Перенаправляет на frontend после социальной авторизации"""
        # Получаем URL для перенаправления из параметра next или используем дефолтный
        next_url = request.GET.get('next', settings.FRONTEND_URL)
        
        # Генерируем JWT токены
        if hasattr(request, 'user') and request.user.is_authenticated:
            refresh = RefreshToken.for_user(request.user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            # Устанавливаем куки с токенами
            response = redirect(next_url)
            response.set_cookie(
                'access_token',
                access_token,
                httponly=True,
                secure=settings.SESSION_COOKIE_SECURE,
                samesite='Lax',
                max_age=3600  # 1 час
            )
            response.set_cookie(
                'refresh_token',
                refresh_token,
                httponly=True,
                secure=settings.SESSION_COOKIE_SECURE,
                samesite='Lax',
                max_age=7 * 24 * 3600  # 7 дней
            )
            return response
            
        return next_url
    
    def is_auto_signup_allowed(self, request, sociallogin):
        """Всегда разрешаем автоматическую регистрацию"""
        return True 