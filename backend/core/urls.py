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
from rest_framework.schemas import get_schema_view
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Создаем главный роутер
router = DefaultRouter()

# Функция для перенаправления на фронтенд после авторизации
def auth_callback(request):
    """Перенаправляет на эндпоинт обработки социальной авторизации"""
    return HttpResponseRedirect(f"/api/accounts/social/callback/?next={settings.FRONTEND_URL}/profile")

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

schema_view = get_schema_view(
   openapi.Info(
      title="Crypto Exchange API",
      default_version='v1',
      description="API documentation for the Crypto Exchange project.",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@example.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

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

    # Swagger/OpenAPI
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Добавляем медиа файлы в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
