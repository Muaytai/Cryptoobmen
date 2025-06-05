from django.utils.deprecation import MiddlewareMixin
from django.middleware.csrf import get_token
from django.conf import settings
import re
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError, AuthenticationFailed
from django.contrib.auth import logout as django_logout
import logging

logger = logging.getLogger(__name__)

class JWTCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()

    def __call__(self, request):
        # САМЫЙ ПЕРВЫЙ ЛОГ: Показывает каждый запрос, проходящий через middleware
        logger.info(f"JWTCookieMiddleware __call__: Path: {request.path}, Method: {request.method}")

        # Пропускаем проверку JWT для определенных путей
        exempt_paths = [
            '/accounts/google/',
            '/accounts/yandex/',
            '/api/accounts/social/',
            '/admin/',
            '/api/auth/login/',
            '/api/auth/register/',
            '/api/auth/verify-email/',
            '/api/auth/resend-email/',
            '/api/auth/password/reset/',
            '/api/auth/password/reset/confirm/',
            '/accounts/google/login/',
            '/accounts/google/login/callback/',
            '/accounts/yandex/login/',
            '/accounts/yandex/login/callback/',
            # '/api/auth/logout/', # Убираем logout из явных исключений здесь, чтобы _set_jwt_auth_header не выполнялся для него ДО LogoutView
        ]
        
        # Пропускаем проверку для путей авторизации, КРОМЕ logout, если он не в exempt_paths явно
        is_exempt_for_set_auth_header = False
        # Проверяем, нужно ли пропускать _set_jwt_auth_header
        # LogoutView сама обработает выход, нам не нужно пытаться аутентифицировать пользователя по JWT перед этим.
        if request.path == '/api/auth/logout/':
            logger.info(f"JWTCookieMiddleware: Path {request.path} is logout, skipping _set_jwt_auth_header initially.")
            is_exempt_for_set_auth_header = True
        else:
            for path_prefix in exempt_paths:
                if request.path.startswith(path_prefix):
                    logger.info(f"JWTCookieMiddleware: Path {request.path} is exempt from _set_jwt_auth_header by prefix {path_prefix}.")
                    is_exempt_for_set_auth_header = True
                    break
        
        if not is_exempt_for_set_auth_header:
            logger.info(f"JWTCookieMiddleware: Path {request.path} is NOT exempt. Calling _set_jwt_auth_header.")
            # Для всех неисключенных путей (включая /api/auth/logout/, если его нет в exempt_paths)
            # сначала проверяем JWT и устанавливаем request.user, если токен валиден
            self._set_jwt_auth_header(request)
        
        response = self.get_response(request)
        
        # Специальная обработка для /api/auth/logout/ ПОСЛЕ того, как LogoutView отработала
        if request.path == '/api/auth/logout/' and request.method == 'POST':
            logger.info(f"JWTCookieMiddleware: Post-processing for /api/auth/logout/. User is: {request.user}")
            # dj_rest_auth.LogoutView уже должна была вызвать django_logout и удалить JWT куки.
            # Дополнительно убедимся, что сессионная кука Django также удалена.
            session_cookie_name = settings.SESSION_COOKIE_NAME
            if session_cookie_name in request.COOKIES:
                logger.info(f"JWTCookieMiddleware: Django session cookie '{session_cookie_name}' found in request to logout. Ensuring it's deleted in response.")
                response.delete_cookie(
                    session_cookie_name,
                    path=settings.SESSION_COOKIE_PATH,
                    domain=settings.SESSION_COOKIE_DOMAIN
                )
            else:
                logger.info(f"JWTCookieMiddleware: Django session cookie '{session_cookie_name}' not found in request to logout. No explicit deletion needed from here.")
            
            # Принудительно удаляем все аутентификационные куки
            logger.info("JWTCookieMiddleware: Forcefully calling _remove_auth_cookies for /api/auth/logout/")
            self._remove_auth_cookies(response, request)

        return response

    def _set_jwt_auth_header(self, request):
        access_token_cookie_name = settings.SIMPLE_JWT['AUTH_COOKIE']
        access_token = request.COOKIES.get(access_token_cookie_name)
        if access_token:
            try:
                validated_token = self.jwt_auth.get_validated_token(access_token)
                user = self.jwt_auth.get_user(validated_token)
                if user:
                    request.user = user
                    request.META['HTTP_AUTHORIZATION'] = f"{settings.SIMPLE_JWT['AUTH_HEADER_TYPES'][0]} {access_token}"
            except (InvalidToken, TokenError, AuthenticationFailed) as e:
                logger.warning(f"JWTCookieMiddleware: Invalid JWT cookie '{access_token_cookie_name}': {e}")
                request.user = None
                if 'HTTP_AUTHORIZATION' in request.META:
                    del request.META['HTTP_AUTHORIZATION']
            except Exception as e:
                logger.error(f"JWTCookieMiddleware: Unexpected error during JWT authentication: {e}")
                request.user = None
                if 'HTTP_AUTHORIZATION' in request.META:
                    del request.META['HTTP_AUTHORIZATION']

    def _remove_auth_cookies(self, response, request):
        logger.info("JWTCookieMiddleware: Attempting to remove authentication cookies.")
        if request.COOKIES:
            logger.info(f"Cookies present in the logout request: {request.COOKIES.keys()}")
        else:
            logger.info("No cookies found in the logout request.")

        cookies_to_delete = [
            settings.SIMPLE_JWT['AUTH_COOKIE'], 
            settings.REST_AUTH.get('JWT_AUTH_REFRESH_COOKIE', 'refresh_token'),
            'sessionid',
            'dj_session_id',
            'csrftoken',
        ]
        
        cookies_to_delete = list(set(cookies_to_delete))
        logger.info(f"JWTCookieMiddleware: Will attempt to delete cookies: {cookies_to_delete}")

        for cookie_name in cookies_to_delete:
            if cookie_name:
                logger.info(f"Deleting cookie: {cookie_name}")
                response.delete_cookie(
                    cookie_name,
                    path=settings.SIMPLE_JWT.get('AUTH_COOKIE_PATH', '/'),
                    domain=settings.SIMPLE_JWT.get('AUTH_COOKIE_DOMAIN', None),
                    samesite=settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax')
                )
        logger.info("JWTCookieMiddleware: Finished attempting to remove cookies.")
        return response


class CsrfCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.csrf_exempt_urls = [re.compile(url) for url in getattr(settings, 'CSRF_EXEMPT_URLS', [])]

    def __call__(self, request):
        path = request.path_info.lstrip('/')
        if any(pattern.match(path) for pattern in self.csrf_exempt_urls):
            request._dont_enforce_csrf_checks = True
        else:
            get_token(request)
        
        response = self.get_response(request)
        return response


class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if 'HTTP_ORIGIN' in request.META:
            origin = request.META['HTTP_ORIGIN']
            if origin in settings.CORS_ALLOWED_ORIGINS:
                response["Access-Control-Allow-Origin"] = origin
                response["Access-Control-Allow-Credentials"] = "true"
                response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
                response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken, Authorization"
        return response 