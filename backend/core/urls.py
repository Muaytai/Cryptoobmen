"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
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

# Создаем главный роутер
router = DefaultRouter()

# Кастомные URL-адреса для регистрации dj_rest_auth, чтобы исправить обработку account-confirm-email
dj_rest_auth_custom_registration_urls = [
    path('', RegisterView.as_view(), name='rest_register'),
    path('verify-email/', VerifyEmailView.as_view(), name='rest_verify_email'),
    path('resend-email/', ResendEmailVerificationView.as_view(), name="rest_resend_email"),
    # Ключевое изменение: используем ConfirmEmailView из allauth
    re_path(r'^account-confirm-email/(?P<key>[-:\w]+)/$', AllauthConfirmEmailView.as_view(), name='account_confirm_email'),
    path('account-email-verification-sent/', 
         TemplateView.as_view(template_name="account/email_verification_sent.html"), # Укажите путь к вашему шаблону, если он есть, или удалите
         name='account_email_verification_sent'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Добавляем URL-адреса allauth. Это должно решить проблему NoReverseMatch для 'account_email'
    path('accounts/', include('allauth.urls')),

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
