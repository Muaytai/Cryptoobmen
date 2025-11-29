from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import redirect
from urllib.parse import urlparse
import logging
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
        # The user object is already populated by allauth.
        # We call the parent method first.
        user = super().save_user(request, user, form, commit=False)

        # Add custom data from the form.
        if hasattr(form, 'cleaned_data'):
            user.phone_number = form.cleaned_data.get('phone_number')

        if commit:
            user.save()
            # Create the user profile
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
        """После логина перенаправляем на backend callback, который выставит JWT-куки, затем на next."""
        from urllib.parse import urlencode
        next_url = request.GET.get('next', settings.FRONTEND_URL + '/profile')
        callback_url = f"{settings.BACKEND_URL}/auth/callback/?{urlencode({'next': next_url})}"
        logging.getLogger(__name__).info(f"CustomAccountAdapter.get_login_redirect_url -> {callback_url}")
        return callback_url
        
    def is_safe_url(self, url):
        """Переопределяем проверку безопасности URL, разрешая все URL"""
        # Разрешаем любой URL для перенаправления
        return True

    def get_email_confirmation_url(self, request, emailconfirmation):
        """Возвращает URL для подтверждения email на фронтенде"""
        # Используем стандартную реализацию allauth для генерации URL
        return super().get_email_confirmation_url(request, emailconfirmation)
    
    def render_mail(self, template_prefix, email, context, headers=None):
        """Переопределяем рендеринг писем, чтобы добавить site_name и site_domain в контекст"""
        # Добавляем правильное название сайта в контекст
        from urllib.parse import urlparse
        frontend_domain = urlparse(settings.FRONTEND_URL).netloc or urlparse(settings.FRONTEND_URL).path
        if not frontend_domain:
            frontend_domain = urlparse(settings.FRONTEND_URL).path.replace('http://', '').replace('https://', '').strip('/')
        
        # Убеждаемся, что site_name и site_domain всегда в контексте
        if 'site_name' not in context:
            context['site_name'] = "TokenX"  # Название вашего сайта
        if 'site_domain' not in context:
            context['site_domain'] = frontend_domain
        
        return super().render_mail(template_prefix, email, context, headers)
    
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
        logger = logging.getLogger(__name__)
        
        # Получаем данные от провайдера
        # В pre_social_login account может быть еще не создан, используем token
        try:
            if hasattr(sociallogin, 'account') and sociallogin.account:
                extra_data = sociallogin.account.extra_data or {}
            elif hasattr(sociallogin, 'token') and sociallogin.token:
                # Пытаемся получить данные из token
                extra_data = sociallogin.token.app.extra_data if hasattr(sociallogin.token, 'app') else {}
            else:
                extra_data = {}
            
            # Для Yandex email может быть в разных полях
            email = extra_data.get('email') or extra_data.get('default_email')
            # Если email в массиве emails, берем первый
            if not email and 'emails' in extra_data and isinstance(extra_data['emails'], list) and len(extra_data['emails']) > 0:
                email = extra_data['emails'][0]
            
            if email:
                try:
                    # Ищем пользователя без учета регистра email
                    user = User.objects.get(email__iexact=email)
                    if not sociallogin.is_existing:
                        # Привязываем существующего пользователя к соцаккаунту
                        sociallogin.connect(request, user)
                except User.DoesNotExist:
                    # Если пользователь не найден, позволяем allauth создать нового
                    pass
        except Exception as e:
            # Логируем неожиданные ошибки с полным traceback
            logger.error("Неожиданная ошибка в pre_social_login", exc_info=True)

    def populate_user(self, request, sociallogin, data):
        """Заполняет данные пользователя из социальной сети"""
        logger = logging.getLogger(__name__)
        
        try:
            user = super().populate_user(request, sociallogin, data)
        except Exception as e:
            logger.error(f"Ошибка в super().populate_user: {str(e)}")
            raise
        
        # Автоматически верифицируем пользователей из соцсетей
        user.is_verified = True
        
        # Получаем данные из соцсети
        # В populate_user account уже должен быть создан
        try:
            if hasattr(sociallogin, 'account') and sociallogin.account:
                extra_data = sociallogin.account.extra_data
                # Убеждаемся, что extra_data - это словарь
                if not isinstance(extra_data, dict):
                    logger.warning(f"extra_data не является словарем: {type(extra_data)}")
                    extra_data = {}
                provider = sociallogin.account.provider
            else:
                logger.warning("sociallogin.account не найден в populate_user")
                extra_data = {}
                provider = None
        except Exception as e:
            logger.error(f"Ошибка при получении данных account: {str(e)}")
            extra_data = {}
            provider = None
        
        # Устанавливаем username до сохранения пользователя
        # Для Yandex email может быть в разных полях
        email = extra_data.get('email') or extra_data.get('default_email') or (user.email if user.email else None)
        # Если email в массиве emails, берем первый
        if not email and 'emails' in extra_data and isinstance(extra_data['emails'], list) and len(extra_data['emails']) > 0:
            email = extra_data['emails'][0]
        
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
        try:
            if provider == 'google':
                if 'picture' in extra_data:
                    try:
                        from django.core.files.base import ContentFile
                        from urllib.request import urlopen
                        avatar_url = extra_data['picture']
                        response = urlopen(avatar_url)
                        uid = sociallogin.account.uid if hasattr(sociallogin, 'account') and sociallogin.account else str(uuid.uuid4())
                        user.avatar.save(
                            f'google_{uid}.jpg',
                            ContentFile(response.read()),
                            save=False
                        )
                    except Exception as e:
                        logger.warning(f"Error saving Google avatar: {str(e)}")
                        
                if 'name' in extra_data:
                    user.full_name = extra_data['name']
                if 'given_name' in extra_data:
                    user.first_name = extra_data['given_name']
                if 'family_name' in extra_data:
                    user.last_name = extra_data['family_name']
                
            elif provider == 'yandex':
                # Логируем данные от Yandex для отладки
                logger.info(f"Yandex extra_data keys: {list(extra_data.keys()) if isinstance(extra_data, dict) else 'not dict'}")
                logger.info(f"Yandex extra_data: {extra_data}")
                
                # Обработка имени
                if 'real_name' in extra_data:
                    user.full_name = extra_data['real_name']
                elif 'display_name' in extra_data:
                    user.full_name = extra_data['display_name']
                
                if 'first_name' in extra_data:
                    user.first_name = extra_data['first_name']
                if 'last_name' in extra_data:
                    user.last_name = extra_data['last_name']
                
                # Обработка аватара для Yandex
                if 'default_avatar_id' in extra_data:
                    try:
                        from django.core.files.base import ContentFile
                        from urllib.request import urlopen
                        # Формируем URL аватара Yandex
                        avatar_url = f"https://avatars.yandex.net/get-yapic/{extra_data['default_avatar_id']}/islands-200"
                        response = urlopen(avatar_url)
                        uid = sociallogin.account.uid if hasattr(sociallogin, 'account') and sociallogin.account else str(uuid.uuid4())
                        user.avatar.save(
                            f'yandex_{uid}.jpg',
                            ContentFile(response.read()),
                            save=False
                        )
                    except Exception as e:
                        logger.warning(f"Error saving Yandex avatar: {str(e)}")
                
                # Убеждаемся, что email установлен
                if not user.email:
                    email = extra_data.get('email') or extra_data.get('default_email')
                    if not email and 'emails' in extra_data and isinstance(extra_data['emails'], list) and len(extra_data['emails']) > 0:
                        email = extra_data['emails'][0]
                    if email:
                        user.email = email
                        logger.info(f"Yandex email установлен: {email}")
                    else:
                        logger.warning("Yandex email не найден в extra_data")
        except Exception as e:
            logger.error(f"Ошибка при обработке данных провайдера {provider}: {str(e)}")
            # Не прерываем выполнение, продолжаем с базовыми данными
        
        return user

    def save_user(self, request, sociallogin, form=None):
        """Сохраняет пользователя, авторизованного через соцсеть"""
        user = super().save_user(request, sociallogin, form)
        
        # Создаем профиль пользователя, если его еще нет
        from accounts.models import UserProfile
        UserProfile.objects.get_or_create(user=user)
        
        # Автоматически подтверждаем email для соцсетей
        from allauth.account.models import EmailAddress
        if user.email:
            email_address, created = EmailAddress.objects.get_or_create(
                user=user,
                email=user.email,
                defaults={'verified': True, 'primary': True}
            )
            if not created:
                email_address.verified = True
                email_address.primary = True
                email_address.save()
        
        # Генерируем JWT токены
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Сохраняем токены в сессии
        request.session['access_token'] = access_token
        request.session['refresh_token'] = refresh_token
        
        return user
    
    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """Не отправляем письма с подтверждением для соцсетей"""
        # Для соцсетей не отправляем письма с подтверждением
        # Email уже подтвержден провайдером
        pass
    
    def get_connect_redirect_url(self, request, socialaccount):
        """Перенаправляет после успешного подключения аккаунта соцсети"""
        next_url = request.GET.get('next')
        if next_url:
            return next_url
        return settings.FRONTEND_URL
    
    def get_login_redirect_url(self, request):
        """Возвращает URL backend callback, который установит JWT-куки и затем перенаправит на next."""
        from urllib.parse import urlencode
        next_url = request.GET.get('next', settings.FRONTEND_URL + '/profile')
        callback_url = f"{settings.BACKEND_URL}/auth/callback/?{urlencode({'next': next_url})}"
        logging.getLogger(__name__).info(f"CustomSocialAccountAdapter.get_login_redirect_url -> {callback_url}")
        return callback_url
    
    def is_auto_signup_allowed(self, request, sociallogin):
        """Всегда разрешаем автоматическую регистрацию"""
        return True 