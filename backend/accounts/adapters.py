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
            # Create the user profile if it doesn't exist
            from accounts.models import UserProfile
            UserProfile.objects.get_or_create(user=user)

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
    
    def get_password_reset_url(self, request, user, temp_key):
        """Возвращает URL для сброса пароля на фронтенде"""
        # temp_key от dj_rest_auth может быть в формате "uidb64-token" или просто token
        # Генерируем uidb64 для пользователя
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Если temp_key содержит дефис, то это "uidb64-token"
        if '-' in temp_key:
            parts = temp_key.split('-', 1)
            uidb64_from_key = parts[0]
            token = parts[1]
            # Используем uidb64 из ключа, если он там есть
            if uidb64_from_key:
                uidb64 = uidb64_from_key
        else:
            # Иначе temp_key - это просто token
            token = temp_key
        
        # Формируем URL на фронтенде
        return f"{settings.FRONTEND_URL}/reset-password/{uidb64}/{token}/"


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Пользовательский адаптер для социальной аутентификации"""
    
    def pre_social_login(self, request, sociallogin):
        """
        Перехватывает социальный логин. Если пользователь с таким email уже существует,
        автоматически связывает аккаунты и выполняет вход, прерывая стандартный
        поток allauth, чтобы избежать страницы регистрации.
        """
        logger = logging.getLogger(__name__)
        
        # Если у sociallogin уже есть pk, значит это существующий пользователь, ничего не делаем
        if sociallogin.user.pk:
            return

        # Ищем email пользователя из разных источников
        email = sociallogin.user.email
        if not email and sociallogin.email_addresses:
            # email_addresses может быть списком или объектом
            if isinstance(sociallogin.email_addresses, list) and len(sociallogin.email_addresses) > 0:
                email = sociallogin.email_addresses[0].email
            elif hasattr(sociallogin.email_addresses, 'email'):
                email = sociallogin.email_addresses.email
        
        # Если email не найден, ищем в extra_data
        if not email and hasattr(sociallogin, 'account') and sociallogin.account:
            extra_data = sociallogin.account.extra_data
            if isinstance(extra_data, dict):
                # Для Yandex email может быть в разных полях
                email = (
                    extra_data.get('email') or 
                    extra_data.get('default_email') or
                    (extra_data.get('emails')[0] if isinstance(extra_data.get('emails'), list) and len(extra_data.get('emails', [])) > 0 else None)
                )
                # Логируем для отладки
                if not email:
                    logger.warning(f"Email не найден в extra_data. Доступные ключи: {list(extra_data.keys())}")
                    logger.debug(f"extra_data содержимое: {extra_data}")
        
        if not email:
            logger.warning("Не удалось получить email от социального провайдера в pre_social_login.")
            return

        try:
            user = User.objects.get(email__iexact=email)
            
            # Если пользователь найден, связываем соц. аккаунт и логиним
            from allauth.exceptions import ImmediateHttpResponse
            from allauth.account.utils import perform_login
            from django.shortcuts import redirect

            logger.info(f"Найден существующий пользователь ('{email}') для социального входа. Связываем аккаунты и выполняем вход.")
            
            # Связываем социальный аккаунт с найденным пользователем
            sociallogin.connect(request, user)
            
            # Выполняем логин
            perform_login(request, user, email_verification='optional')
            
            # Прерываем стандартный поток и делаем редирект
            redirect_url = self.get_login_redirect_url(request)
            raise ImmediateHttpResponse(redirect(redirect_url))

        except User.DoesNotExist:
            # Пользователь не найден, продолжаем стандартный процесс регистрации
            logger.info(f"Пользователь с email '{email}' не найден. Продолжаем стандартную регистрацию через соцсеть.")
            pass
        except Exception as e:
            # Добавим логгирование самой ошибки
            logger.error(f"Неожиданная ошибка в pre_social_login: {e}", exc_info=True)

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
            email = extra_data['emails'][0] if isinstance(extra_data['emails'][0], str) else extra_data['emails'][0].get('value', '')
        
        # Убеждаемся, что email - это строка
        if email and not isinstance(email, str):
            email = str(email)
        
        if email:
            # Извлекаем часть email до @ и обрезаем до 150 символов (максимальная длина username в Django)
            base_username = email.split('@')[0] if '@' in email else email
            # Если base_username пустой, используем часть email до @
            if not base_username:
                base_username = 'user'
            # Обрезаем до 150 символов, чтобы избежать обрезки при сохранении
            # Оставляем место для суффикса с числом (например, "123")
            max_base_length = 147  # 150 - 3 символа для суффикса
            if len(base_username) > max_base_length:
                base_username = base_username[:max_base_length]
            username = base_username
            counter = 1
            # Проверяем существование username и добавляем число если занят
            while User.objects.filter(username=username).exists():
                # Обрезаем base_username еще больше, чтобы поместить число
                suffix = str(counter)
                max_with_suffix = 150 - len(suffix)
                if len(base_username) > max_with_suffix:
                    base_username = base_username[:max_with_suffix]
                username = f"{base_username}{suffix}"
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
                    # Если email в массиве emails, берем первый элемент
                    if not email and 'emails' in extra_data:
                        if isinstance(extra_data['emails'], list) and len(extra_data['emails']) > 0:
                            email = extra_data['emails'][0] if isinstance(extra_data['emails'][0], str) else extra_data['emails'][0].get('value', '')
                        elif isinstance(extra_data['emails'], str):
                            email = extra_data['emails']
                    
                    if email:
                        user.email = email
                        logger.info(f"Yandex email установлен: {email}")
                    else:
                        logger.warning("Yandex email не найден в extra_data")
                        logger.warning(f"Доступные ключи в extra_data: {list(extra_data.keys())}")
                        logger.debug(f"Полное содержимое extra_data: {extra_data}")
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
        """Всегда разрешаем автоматическую регистрацию, т.к. pre_social_login обрабатывает случай существующего пользователя."""
        return True