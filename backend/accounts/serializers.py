from rest_framework import serializers
from django.conf import settings
import requests
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
    recaptcha_token = serializers.CharField(required=True, write_only=True)
    
    def get_cleaned_data(self):
        return {
            'password': self.validated_data.get('password1', ''),
            'email': self.validated_data.get('email', ''),
            'username': self.validated_data.get('username', ''),
            'phone_number': self.validated_data.get('phone_number', ''),
        }
    
    def validate(self, attrs):
        """Проверяем reCAPTCHA перед валидацией"""
        recaptcha_token = attrs.get('recaptcha_token')
        
        if not recaptcha_token:
            raise serializers.ValidationError('Токен reCAPTCHA обязателен.')
        
        # Проверяем reCAPTCHA
        request = self.context.get('request')
        client_ip = None
        if request:
            client_ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] or request.META.get('REMOTE_ADDR')
        
        # Используем тот же метод проверки, что и в CustomLoginSerializer
        self._verify_recaptcha(recaptcha_token, expected_action='register', remote_ip=client_ip)
        
        return attrs
    
    def _verify_recaptcha(self, token: str, expected_action: str, remote_ip: str | None = None) -> None:
        """Проверяет reCAPTCHA v3 токен через серверный endpoint."""
        from django.conf import settings
        import requests
        
        secret_key = getattr(settings, 'RECAPTCHA_PRIVATE_KEY', '')
        required_score = float(getattr(settings, 'RECAPTCHA_REQUIRED_SCORE', 0.85))
        recaptcha_domain = getattr(settings, 'RECAPTCHA_DOMAIN', 'www.recaptcha.net')

        if not secret_key:
            raise serializers.ValidationError('Серверная проверка reCAPTCHA не настроена.')

        verify_url = f"https://{recaptcha_domain}/recaptcha/api/siteverify"
        data = {
            'secret': secret_key,
            'response': token,
        }
        if remote_ip:
            data['remoteip'] = remote_ip

        try:
            resp = requests.post(verify_url, data=data, timeout=5)
            resp.raise_for_status()
            payload = resp.json()
        except Exception:
            raise serializers.ValidationError('Ошибка проверки reCAPTCHA. Попробуйте позже.')

        if not payload.get('success'):
            raise serializers.ValidationError('Проверка reCAPTCHA не пройдена.')

        action = payload.get('action')
        score = payload.get('score', 0)

        if action and expected_action and action != expected_action:
            raise serializers.ValidationError('Неверное действие reCAPTCHA.')

        if score < required_score:
            raise serializers.ValidationError('Слишком низкий балл reCAPTCHA.')


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


class CustomLoginSerializer(serializers.Serializer):
    """
    Полностью кастомный сериализатор для входа по email.
    Наследуется от базового Serializer для полного контроля.
    """
    email = serializers.EmailField(required=True, write_only=True)
    password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False, write_only=True)
    recaptcha_token = serializers.CharField(required=True, write_only=True)

    def _verify_recaptcha(self, token: str, expected_action: str, remote_ip: str | None = None) -> None:
        """Проверяет reCAPTCHA v3 токен через серверный endpoint.

        Поднимает ValidationError при некорректной проверке.
        """
        secret_key = getattr(settings, 'RECAPTCHA_PRIVATE_KEY', '')
        required_score = float(getattr(settings, 'RECAPTCHA_REQUIRED_SCORE', 0.85))
        recaptcha_domain = getattr(settings, 'RECAPTCHA_DOMAIN', 'www.recaptcha.net')

        if not secret_key:
            raise serializers.ValidationError('Серверная проверка reCAPTCHA не настроена.')

        verify_url = f"https://{recaptcha_domain}/recaptcha/api/siteverify"
        data = {
            'secret': secret_key,
            'response': token,
        }
        if remote_ip:
            data['remoteip'] = remote_ip

        try:
            resp = requests.post(verify_url, data=data, timeout=5)
            resp.raise_for_status()
            payload = resp.json()
        except Exception:
            raise serializers.ValidationError('Ошибка проверки reCAPTCHA. Попробуйте позже.')

        if not payload.get('success'):
            raise serializers.ValidationError('Проверка reCAPTCHA не пройдена.')

        action = payload.get('action')
        score = payload.get('score', 0)

        if action and expected_action and action != expected_action:
            raise serializers.ValidationError('Неверное действие reCAPTCHA.')

        if score < required_score:
            raise serializers.ValidationError('Слишком низкий балл reCAPTCHA.')

    def validate(self, attrs):
        email = attrs.get('email').lower()
        password = attrs.get('password')
        recaptcha_token = attrs.get('recaptcha_token')

        if not email or not password:
            raise serializers.ValidationError(
                'Пожалуйста, укажите email и пароль.',
                code='authorization',
            )

        request = self.context.get('request')

        # Проверяем reCAPTCHA перед аутентификацией
        client_ip = None
        if request:
            # Стандартные заголовки для реального IP за прокси/балансировщиком
            client_ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] or request.META.get('REMOTE_ADDR')
        self._verify_recaptcha(recaptcha_token, expected_action='login', remote_ip=client_ip)
        user = authenticate(request=request, username=email, password=password)

        if not user:
            raise serializers.ValidationError(
                'Невозможно войти в систему с указанными учетными данными.',
                code='authorization',
            )

        attrs['user'] = user
        return attrs