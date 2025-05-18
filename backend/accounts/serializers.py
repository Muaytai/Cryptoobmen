from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from allauth.account.adapter import get_adapter
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer
from .models import UserProfile, UserDocument

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля пользователя"""
    
    class Meta:
        model = UserProfile
        fields = ['bio', 'website', 'language', 'dark_mode']
        read_only_fields = ['id']


class UserDetailsSerializer(serializers.ModelSerializer):
    """Расширенный сериализатор для пользователя"""
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 
            'avatar', 'phone_number', 'is_verified', 'kyc_verified',
            'telegram_id', 'date_joined', 'profile', 'has_2fa',
            'notify_via_email', 'notify_via_telegram'
        ]
        read_only_fields = ['id', 'email', 'date_joined', 'is_verified', 'kyc_verified']


class CustomRegisterSerializer(RegisterSerializer):
    """Сериализатор для регистрации с дополнительными полями"""
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    
    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data.update({
            'phone_number': self.validated_data.get('phone_number', ''),
        })
        return data


class UserDocumentSerializer(serializers.ModelSerializer):
    """Сериализатор для документов пользователя (KYC)"""
    
    class Meta:
        model = UserDocument
        fields = ['id', 'document_type', 'document_file', 'uploaded_at', 'status']
        read_only_fields = ['id', 'uploaded_at', 'status']
    
    def create(self, validated_data):
        """Добавляет текущего пользователя к документу"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления данных пользователя"""
    profile = UserProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'avatar', 'phone_number',
            'full_name', 'date_of_birth', 'address', 'profile',
            'notify_via_email', 'notify_via_telegram', 'telegram_id',
        ]
    
    def update(self, instance, validated_data):
        """Обновляет пользователя и его профиль"""
        profile_data = validated_data.pop('profile', None)
        
        # Обновляем пользователя
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Обновляем профиль, если есть данные
        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance 


class CustomLoginSerializer(LoginSerializer):
    """Кастомный сериализатор для логина, использующий email вместо username"""
    username = None  # Отключаем поле username
    email = serializers.EmailField(required=True)
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        # Здесь переносим email в поле username для стандартной аутентификации
        email = attrs.get('email')
        password = attrs.get('password')
        
        # Проверяем, что email и пароль указаны
        if email and password:
            # Подготавливаем данные для стандартной аутентификации
            attrs['username'] = email  # Django будет искать пользователя по username
            return super().validate(attrs)
        else:
            msg = 'Необходимо указать "email" и "password".'
            raise serializers.ValidationError(msg, code='authorization') 