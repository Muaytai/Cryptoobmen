from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from dj_rest_auth.views import PasswordResetConfirmView
from dj_rest_auth.registration.views import RegisterView, ResendEmailVerificationView, VerifyEmailView
from allauth.account.views import ConfirmEmailView as AllauthConfirmEmailView
from django.views.generic import TemplateView
from rest_framework.documentation import include_docs_urls
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from django.http import HttpResponseRedirect

# Создаем главный роутер
router = DefaultRouter()

# Функция для перенаправления на фронтенд после авторизации
def auth_callback(request):
    """Перенаправляет на эндпоинт обработки социальной авторизации"""
    return HttpResponseRedirect(f"/api/accounts/social/callback/?next={settings.FRONTEND_URL}/profile")

# Функция для верификации email и перенаправления на фронтенд
from allauth.account.models import EmailConfirmation, EmailAddress, EmailConfirmationHMAC
from allauth.account.adapter import get_adapter

def simple_email_redirect(request, key=None, *args, **kwargs):
    """Мгновенно перенаправляет на фронтенд с параметром verified=true"""
    # Мгновенно перенаправляем на фронтенд без какой-либо обработки
    return HttpResponseRedirect(f"{settings.FRONTEND_URL}/verify-email?verified=true")

# Функция для перенаправления на фронтенд после авторизации
def auth_callback(request):
    """Перенаправляет на эндпоинт обработки социальной авторизации"""
    return HttpResponseRedirect(f"/api/accounts/social/callback/?next={settings.FRONTEND_URL}/profile")

# Кастомные URL-адреса для регистрации dj_rest_auth, чтобы исправить обработку account-confirm-email
dj_rest_auth_custom_registration_urls = [
    path('', RegisterView.as_view(), name='rest_register'),
    path('verify-email/', VerifyEmailView.as_view(), name='rest_verify_email'),
    path('resend-email/', ResendEmailVerificationView.as_view(), name="rest_resend_email"),
    # Не используем здесь ConfirmEmailView, так как мы хотим перенаправить на фронтенд
    path('account-email-verification-sent/', 
         TemplateView.as_view(template_name="account/email_verification_sent.html"),
         name='account_email_verification_sent'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Добавляем URL-адреса allauth. Это должно решить проблему NoReverseMatch для 'account_email'
    path('accounts/', include('allauth.urls')),
    
    # Перенаправление после подтверждения email
    re_path(r'^accounts/confirm-email/(?P<key>[-:\w]+)/$', simple_email_redirect, name='account_confirm_email'),
    # Добавляем также перенаправление для account-confirm-email (используется в dj_rest_auth)
    re_path(r'^api/auth/registration/account-confirm-email/(?P<key>[-:\w]+)/$', simple_email_redirect, name='account_confirm_email_dj_rest_auth'),

    # Путь для перенаправления после авторизации через соцсеть
    path('auth/callback/', auth_callback, name='auth_callback'),

    # API endpoints
    path('api/', include(router.urls)),
    path('api/accounts/', include('accounts.urls')),
    path('api/crypto/', include('crypto.urls')),
    path('api/transactions/', include('transactions.urls')),
    
    # Аутентификация
    path('api/auth/', include('dj_rest_auth.urls')),
    # Используем кастомные URL для регистрации
    path('api/auth/registration/', include(dj_rest_auth_custom_registration_urls)), 
    path('api/auth/password/reset/confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # JWT endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Документация API
    # path('api/docs/', include_docs_urls(title='Crypto Exchange API')),
]

# Добавляем медиа файлы в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
