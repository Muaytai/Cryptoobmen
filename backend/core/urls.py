from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from dj_rest_auth.views import PasswordResetConfirmView, LogoutView, UserDetailsView
from accounts.views import CustomLoginView
from dj_rest_auth.registration.views import RegisterView, ResendEmailVerificationView, VerifyEmailView
from django.views.generic import TemplateView
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from django.http import HttpResponseRedirect
import logging
from urllib.parse import urlencode
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# Создаем главный роутер
router = DefaultRouter()

# Функция для перенаправления на фронтенд после авторизации
logger = logging.getLogger(__name__)

def auth_callback(request):
    """Перенаправляет на обработчик социальной авторизации и пробрасывает next из запроса."""
    next_param = request.GET.get('next', f"{settings.FRONTEND_URL}/profile")
    logger.info(f"auth_callback: received, user.is_authenticated={getattr(request, 'user', None) and request.user.is_authenticated}, next={next_param}")
    query = urlencode({'next': next_param})
    redirect_url = f"/api/accounts/social/callback/?{query}"
    logger.info(f"auth_callback: redirecting to {redirect_url}")
    return HttpResponseRedirect(redirect_url)

# Кастомные URL-адреса для регистрации dj_rest_auth
dj_rest_auth_custom_registration_urls = [
    path('', RegisterView.as_view(permission_classes=(permissions.AllowAny,)), name='rest_register'),
    path('verify-email/', VerifyEmailView.as_view(), name='rest_verify_email'),
    path('resend-email/', ResendEmailVerificationView.as_view(), name="rest_resend_email"),
    # Путь для страницы "письмо отправлено"
    path('account-email-verification-sent/', 
         TemplateView.as_view(template_name="account/email_verification_sent.html"),
         name='account_email_verification_sent'),
]

# --- Блок schema_view для drf-yasg (удален) ---
# Вся эта конфигурация теперь находится в SPECTACULAR_SETTINGS в вашем файле settings.py

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # URL-адреса allauth, включая /accounts/confirm-email/<key>/
    path('accounts/', include('allauth.urls')),
    
    # Путь для перенаправления после авторизации через соцсеть
    path('auth/callback/', auth_callback, name='auth_callback'),

    # API endpoints
    path('api/', include(router.urls)),
    path('api/accounts/', include('accounts.urls')),
    path('api/crypto/', include('crypto.urls')),
    path('api/transactions/', include('transactions.urls')),
    
    # Аутентификация
    path('api/auth/login/', CustomLoginView.as_view(), name='rest_login'),
    path('api/auth/logout/', LogoutView.as_view(), name='rest_logout'),
    path('api/auth/user/', UserDetailsView.as_view(), name='rest_user_details'),
    # Используем кастомные URL для регистрации
    path('api/auth/registration/', include(dj_rest_auth_custom_registration_urls)), 
    path('api/auth/password/reset/confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # JWT endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # --- Новые URL-адреса для документации API (drf-spectacular) ---
    # URL для скачивания файла schema.yml (это основной источник данных для UI)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # URL для интерактивной документации Swagger UI (рекомендуется)
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # URL для альтернативной документации Redoc
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Добавляем медиа файлы в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)