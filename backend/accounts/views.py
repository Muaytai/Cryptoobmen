from django.shortcuts import render
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    UserDetailsSerializer, UserDocumentSerializer, UserUpdateSerializer,
    CustomLoginSerializer,
    UserProfileSerializer, UserDetailedInfoSerializer, UserWithBalanceSerializer
)
from .models import UserDocument, UserProfile
from .decorators import site_admin_required, site_admin_or_staff_required
from .mixins import SiteAdminRequiredMixin, SiteAdminOrStaffRequiredMixin
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.http import HttpResponseRedirect
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

from dj_rest_auth.views import LoginView as RestAuthLoginView

class CustomLoginView(RestAuthLoginView):
    serializer_class = CustomLoginSerializer

class UserViewSet(viewsets.ModelViewSet):
    """API для работы с пользователями"""
    queryset = User.objects.all()
    serializer_class = UserDetailsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Пользователь может видеть только свой профиль"""
        if self.request.user.is_staff or self.request.user.is_site_admin:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action == 'update' or self.action == 'partial_update':
            return UserUpdateSerializer
        return UserDetailsSerializer
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Возвращает информацию о текущем пользователе"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        """Обновляет профиль пользователя"""
        user = request.user
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def detailed_info(self, request, pk=None):
        """Возвращает детальную информацию о пользователе включая кошельки и транзакции (только для админов)"""
        if not (request.user.is_staff or request.user.is_site_admin):
            return Response(
                {"error": "У вас нет прав для просмотра детальной информации пользователей"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        serializer = UserDetailedInfoSerializer(user, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def admin_list(self, request):
        """Возвращает список пользователей с балансами для админов"""
        if not (request.user.is_staff or request.user.is_site_admin):
            return Response(
                {"error": "У вас нет прав для просмотра списка пользователей"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        users = User.objects.all()
        serializer = UserWithBalanceSerializer(users, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Возвращает статистику для дашборда администратора"""
        if not (request.user.is_staff or request.user.is_site_admin):
            return Response(
                {"error": "У вас нет прав для просмотра статистики"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Импортируем модели здесь, чтобы избежать циклических импортов
        from crypto.models import UserWallet, Cryptocurrency, ExchangePair
        from transactions.models import Transaction
        
        now = timezone.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        
        # Статистика пользователей
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        verified_users = User.objects.filter(is_verified=True).count()
        kyc_verified_users = User.objects.filter(kyc_verified=True).count()
        new_users_today = User.objects.filter(date_joined__gte=today).count()
        
        # Статистика транзакций
        total_transactions = Transaction.objects.count()
        pending_transactions = Transaction.objects.filter(
            status__in=['pending', 'processing']
        ).count()
        completed_transactions = Transaction.objects.filter(status='completed').count()
        failed_transactions = Transaction.objects.filter(status='failed').count()
        
        # Объемы торгов
        volume_24h = Transaction.objects.filter(
            timestamp__gte=yesterday,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        volume_7d = Transaction.objects.filter(
            timestamp__gte=week_ago,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Статистика кошельков
        total_wallets = UserWallet.objects.count()
        active_currencies = UserWallet.objects.values('currency').distinct().count()
        
        # Общий баланс в USD (упрощенный расчет)
        total_balance_usd = 0
        for wallet in UserWallet.objects.select_related('currency').all():
            if wallet.currency and hasattr(wallet.currency, 'prices'):
                latest_price = wallet.currency.prices.first()
                if latest_price:
                    total_balance_usd += float(wallet.balance) * float(latest_price.price_usd)
        
        # Системная статистика
        active_cryptocurrencies = Cryptocurrency.objects.filter(is_active=True).count()
        total_exchange_pairs = ExchangePair.objects.count()
        
        # Определяем здоровье системы
        system_health = 'good'
        if total_transactions > 0:
            failure_rate = failed_transactions / total_transactions
            if failure_rate > 0.2:
                system_health = 'critical'
            elif failure_rate > 0.1:
                system_health = 'warning'
        
        return Response({
            'users': {
                'total': total_users,
                'active': active_users,
                'verified': verified_users,
                'kyc_verified': kyc_verified_users,
                'new_today': new_users_today,
            },
            'transactions': {
                'total': total_transactions,
                'pending': pending_transactions,
                'completed': completed_transactions,
                'failed': failed_transactions,
                'volume_24h': float(volume_24h),
                'volume_7d': float(volume_7d),
            },
            'wallets': {
                'total': total_wallets,
                'total_balance_usd': total_balance_usd,
                'active_currencies': active_currencies,
            },
            'system': {
                'active_cryptocurrencies': active_cryptocurrencies,
                'total_exchange_pairs': total_exchange_pairs,
                'system_health': system_health,
            }
        })


class UserDocumentViewSet(viewsets.ModelViewSet):
    """API для работы с KYC документами пользователя"""
    serializer_class = UserDocumentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Пользователь видит свои документы, site-admin/staff могут видеть по user параметру"""
        user = self.request.user
        if getattr(user, 'is_site_administrator', lambda: False)() or user.is_staff:
            target_user_id = self.request.query_params.get('user')
            if target_user_id:
                return UserDocument.objects.filter(user_id=target_user_id)
            return UserDocument.objects.all()
        return UserDocument.objects.filter(user=user)


class UserProfileViewSet(viewsets.ModelViewSet):
    """API для работы с профилем пользователя"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Пользователь может видеть только свой профиль"""
        return UserProfile.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['patch'])
    def toggle_theme(self, request):
        """Переключает темную/светлую тему"""
        profile = request.user.profile
        profile.dark_mode = not profile.dark_mode
        profile.save()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    def set_language(self, request):
        """Устанавливает язык интерфейса"""
        profile = request.user.profile
        language = request.data.get('language', 'ru')
        profile.language = language
        profile.save()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

def get_tokens_for_user(user):
    """Создаёт JWT токены для пользователя"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

@method_decorator(csrf_exempt, name='dispatch')
class SocialLoginCallbackView(View):
    """Обрабатывает коллбэк после успешной авторизации через соцсеть"""
    
    def get(self, request, *args, **kwargs):
        """Обрабатывает GET запрос после авторизации через соцсеть"""
        try:
            # Получаем URL для перенаправления из параметра next или используем дефолтный
            next_url = request.GET.get('next', f"{settings.FRONTEND_URL}/profile")
            
            # Если пользователь авторизован, генерируем JWT токены
            if request.user.is_authenticated:
                tokens = get_tokens_for_user(request.user)
                
                # Создаем response для редиректа
                response = HttpResponseRedirect(next_url)
                
                # Устанавливаем куки с токенами
                response.set_cookie(
                    settings.SIMPLE_JWT['AUTH_COOKIE'],
                    tokens['access'],
                    max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                    path='/',
                    httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                    samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                    secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE']
                )
                
                response.set_cookie(
                    'refresh_token',
                    tokens['refresh'],
                    max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                    path='/',
                    httponly=True,
                    samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                    secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE']
                )
                
                logger.info(f"Успешная авторизация через соцсеть для пользователя {request.user.email}")
                return response
            
            # Если пользователь не авторизован, перенаправляем на страницу входа
            logger.warning("Попытка социальной авторизации без пользователя")
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/login?error=auth_failed")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке социальной авторизации: {str(e)}")
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/login?error=server_error")


# Примеры использования декораторов и миксинов для администраторов сайта

@api_view(['GET'])
@site_admin_required
def admin_dashboard(request):
    """Пример представления только для администраторов сайта"""
    return Response({
        'message': 'Добро пожаловать в панель администратора сайта!',
        'user': request.user.email,
        'is_site_admin': request.user.is_site_admin,
        'is_superuser': request.user.is_superuser
    })


@api_view(['GET'])
@site_admin_or_staff_required
def admin_or_staff_dashboard(request):
    """Пример представления для администраторов сайта или персонала"""
    return Response({
        'message': 'Добро пожаловать в панель управления!',
        'user': request.user.email,
        'is_site_admin': request.user.is_site_admin,
        'is_staff': request.user.is_staff,
        'is_superuser': request.user.is_superuser
    })


class AdminOnlyViewSet(SiteAdminRequiredMixin, viewsets.ModelViewSet):
    """Пример ViewSet только для администраторов сайта"""
    queryset = User.objects.all()
    serializer_class = UserDetailsSerializer
    
    def list(self, request, *args, **kwargs):
        """Список всех пользователей - только для администраторов сайта"""
        return super().list(request, *args, **kwargs)


class AdminOrStaffViewSet(SiteAdminOrStaffRequiredMixin, viewsets.ModelViewSet):
    """Пример ViewSet для администраторов сайта или персонала"""
    queryset = UserDocument.objects.all()
    serializer_class = UserDocumentSerializer
    
    def list(self, request, *args, **kwargs):
        """Список всех документов - для администраторов сайта или персонала"""
        return super().list(request, *args, **kwargs)
