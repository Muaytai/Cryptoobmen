from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Расширенная модель пользователя для криптоплатформы"""
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(_('phone number'), max_length=15, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    telegram_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Дополнительные поля для KYC
    kyc_verified = models.BooleanField(default=False)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Для отправки уведомлений
    notify_via_email = models.BooleanField(default=True)
    notify_via_telegram = models.BooleanField(default=False)
    
    # Права администратора сайта (отдельно от is_staff)
    is_site_admin = models.BooleanField(
        default=False,
        verbose_name=_('Site Administrator'),
        help_text=_('Designates this user as a site administrator who can manage the platform.')
    )
    
    # Дата последнего входа
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    
    # Переопределяем поля groups и user_permissions с уникальными related_name
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to. A user will get all permissions granted to each of their groups.'),
        related_name='custom_user_set',
        related_query_name='custom_user'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='custom_user_set',
        related_query_name='custom_user'
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
    
    def __str__(self):
        return self.email
    
    @property
    def full_name_display(self):
        """Возвращает полное имя пользователя или username"""
        if self.full_name:
            return self.full_name
        return self.username
    
    def is_site_administrator(self):
        """Проверяет, является ли пользователь администратором сайта"""
        return self.is_site_admin or self.is_superuser


class UserProfile(models.Model):
    """Профиль пользователя с дополнительной информацией"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    language = models.CharField(max_length=10, default='ru')
    dark_mode = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Профиль {self.user.email}"


class UserDocument(models.Model):
    """Документы пользователя для KYC верификации"""
    DOCUMENT_TYPES = (
        ('passport', _('Passport')),
        ('driver_license', _('Driver License')),
        ('id_card', _('ID Card')),
    )
    
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_file = models.FileField(upload_to='user_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.document_type} документ для {self.user.email}"
