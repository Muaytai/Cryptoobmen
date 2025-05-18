from django.utils.deprecation import MiddlewareMixin
from django.middleware.csrf import get_token
from django.conf import settings
import re
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import logout


class JWTCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()

    def __call__(self, request):
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
        ]
        
        # Пропускаем проверку для путей авторизации
        if any(request.path.startswith(path) for path in exempt_paths):
            return self.get_response(request)
            
        # Для остальных путей проверяем JWT
        self._set_jwt_auth_header(request)
        response = self.get_response(request)
        
        # Если это запрос на выход
        if request.path == '/api/auth/logout/' and request.method == 'POST':
            self._remove_auth_cookies(response)
            request.session.flush()
            logout(request)
            if 'HTTP_AUTHORIZATION' in request.META:
                del request.META['HTTP_AUTHORIZATION']
            request.user = None
            response.status_code = 200
            response.data = {'detail': 'Successfully logged out'}
        
        return response

    def _set_jwt_auth_header(self, request):
        access_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])
        if access_token:
            try:
                validated_token = self.jwt_auth.get_validated_token(access_token)
                user = self.jwt_auth.get_user(validated_token)
                request.user = user
                request.META['HTTP_AUTHORIZATION'] = f"{settings.SIMPLE_JWT['AUTH_HEADER_TYPES'][0]} {access_token}"
            except (InvalidToken, TokenError):
                self._remove_auth_cookies(request)
                request.user = None

    def _remove_auth_cookies(self, response):
        cookies_to_delete = [
            'access_token',
            'refresh_token',
            'sessionid',
            'dj_session_id',
            'csrftoken',
            'auth_token',
            'next_hmr_refresh_hash'
        ]
        
        for cookie in cookies_to_delete:
            if cookie:
                response.delete_cookie(
                    cookie,
                    path='/',
                    domain=None,
                    samesite='Lax'
                )
        
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