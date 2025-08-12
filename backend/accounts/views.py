from django.shortcuts import render
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    UserDetailsSerializer, UserDocumentSerializer, UserUpdateSerializer,
    CustomLoginSerializer,
    UserProfileSerializer
)
from .models import UserDocument, UserProfile
from django.db.models import Q
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
        if self.request.user.is_staff:
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
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDocumentViewSet(viewsets.ModelViewSet):
    """API для работы с KYC документами пользователя"""
    serializer_class = UserDocumentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Пользователь может видеть только свои документы"""
        return UserDocument.objects.filter(user=self.request.user)


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
