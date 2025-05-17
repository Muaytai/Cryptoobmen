from django.utils.deprecation import MiddlewareMixin
from django.middleware.csrf import get_token
from django.conf import settings
import re


class CsrfCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Компилируем регулярные выражения один раз при инициализации
        self.csrf_exempt_urls = [re.compile(url) for url in getattr(settings, 'CSRF_EXEMPT_URLS', [])]

    def __call__(self, request):
        # Проверяем, подпадает ли URL под исключения CSRF
        path = request.path_info.lstrip('/')
        if any(pattern.match(path) for pattern in self.csrf_exempt_urls):
            request._dont_enforce_csrf_checks = True
        else:
            # Для всех остальных запросов устанавливаем CSRF токен
            get_token(request)
        
        response = self.get_response(request)
        return response


class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Access-Control-Allow-Origin"] = "http://localhost:3000"
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken, Authorization"
        return response 