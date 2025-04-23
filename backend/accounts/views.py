from django.shortcuts import render
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    UserDetailsSerializer, UserDocumentSerializer, UserUpdateSerializer,
    UserProfileSerializer
)
from .models import UserDocument, UserProfile
from django.db.models import Q
from django.conf import settings

User = get_user_model()


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
