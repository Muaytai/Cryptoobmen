
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from crypto.models import Cryptocurrency, UserWallet
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail


class Transaction(models.Model):
    """Основная модель для всех транзакций"""
    TYPE_CHOICES = (
        ('deposit', _('Депозит')),
        ('withdrawal', _('Вывод')),
        ('exchange', _('Обмен')),
        ('transfer', _('Перевод')),
        ('fee', _('Комиссия')),
        ('consolidation', _('Консолидация')),
    )
    
    STATUS_CHOICES = (
        ('pending', _('В ожидании')),
        ('awaiting_confirmation', _('Ожидает подтверждения')),
        ('processing', _('В обработке')),
        ('completed', _('Завершено')),
        ('failed', _('Ошибка')),
        ('cancelled', _('Отменено')),
        ('refunded', _('Возвращено')),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    
    amount = models.DecimalField(max_digits=24, decimal_places=8)
    fee = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    
    crypto = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, related_name='transactions')
    
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Сетевая информация (для blockchain транзакций)
    tx_hash = models.CharField(max_length=255, blank=True, null=True, unique=True)
    block_number = models.IntegerField(blank=True, null=True)
    
    # Дополнительная информация
    notes = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.amount} {self.crypto.symbol} - {self.user.username}"
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = _('transaction')
        verbose_name_plural = _('transactions')


class Exchange(models.Model):
    """Модель для обмена криптовалют"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exchanges')
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='exchange')
    
    # От какой криптовалюты к какой
    from_crypto = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, related_name='exchanges_from')
    to_crypto = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, related_name='exchanges_to')
    
    # Количество и стоимость
    from_amount = models.DecimalField(max_digits=24, decimal_places=8)
    to_amount = models.DecimalField(max_digits=24, decimal_places=8)
    rate = models.DecimalField(max_digits=24, decimal_places=8)
    
    # Комиссия
    fee_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    fee_amount = models.DecimalField(max_digits=24, decimal_places=8)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.from_amount} {self.from_crypto.symbol} -> {self.to_amount} {self.to_crypto.symbol}"
    
    class Meta:
        ordering = ['-timestamp']


class Deposit(models.Model):
    """Модель для депозитов"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deposits')
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='deposit')
    
    wallet = models.ForeignKey(
        UserWallet,
        on_delete=models.CASCADE,
        related_name='deposits',
        null=True
    )
    address = models.CharField(max_length=255, null=True, blank=True)
    
    confirmed = models.BooleanField(default=False)
    confirmation_date = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        currency_symbol = self.wallet.currency.symbol if self.wallet and self.wallet.currency else "N/A"
        return f"Deposit {self.transaction.amount} {currency_symbol} to {self.address}"


class Withdrawal(models.Model):
    """Модель для вывода средств"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='withdrawals')
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='withdrawal')
    
    wallet = models.ForeignKey(
        UserWallet,
        on_delete=models.CASCADE,
        related_name='withdrawals',
        null=True
    )
    destination_address = models.CharField(max_length=255)
    memo = models.CharField(max_length=255, blank=True, null=True, verbose_name='MEMO/Tag')

    # Поля для подтверждения вывода
    is_email_confirmed = models.BooleanField(default=False, verbose_name=_("Email Confirmed"))
    email_confirmation_token = models.UUIDField(null=True, blank=True, verbose_name=_("Email Confirmation Token"))
    email_confirmation_token_expires_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Email Token Expires At"))

    # Статусы подтверждения
    confirmed_by_admin = models.BooleanField(default=False)
    rejected_reason = models.TextField(blank=True, null=True)
    
    # Время подтверждения
    confirmation_date = models.DateTimeField(blank=True, null=True)
    
    refunded = models.BooleanField(default=False)
    
    @property
    def status(self):
        return self.transaction.status

    @status.setter
    def status(self, value):
        if self.transaction.status != value:
            self.transaction.status = value
            self.transaction.save()
    
    def __str__(self):
        currency_symbol = self.wallet.currency.symbol if self.wallet and self.wallet.currency else "N/A"
        amount_display = self.transaction.amount if self.transaction else "N/A"
        return f"Withdrawal {amount_display} {currency_symbol} to {self.destination_address}"


class Transfer(models.Model):
    """Модель перевода средств между кошельками / системными счетами.
    Используется задачами `crypto.tasks` и тестами.
    """

    class Status(models.TextChoices):
        PENDING = "pending", _("В ожидании")
        SUCCESS = "success", _("Успешно")
        FAILED = "failed", _("Ошибка")

    TYPE_CHOICES = (
        ("in", _("Входящий")),
        ("out", _("Исходящий")),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transfers",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    type = models.CharField(max_length=3, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    fee = models.DecimalField(max_digits=24, decimal_places=8, null=True, blank=True)
    tx_hash = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    withdrawal = models.OneToOneField(
        'Withdrawal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transfer'
    )
 
    def __str__(self):
        return f"Transfer {self.id} {self.get_type_display()} {self.amount} - {self.status}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("transfer")
        verbose_name_plural = _("transfers")


class Review(models.Model):
    """Модель для отзывов пользователей"""
    RATING_CHOICES = (
        (1, '1 - Ужасно'),
        (2, '2 - Плохо'),
        (3, '3 - Нормально'),
        (4, '4 - Хорошо'),
        (5, '5 - Отлично'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='reviews',
        null=True,
        blank=True,
        verbose_name=_('User')
    )
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    email = models.EmailField(verbose_name=_('Email'))
    rating = models.IntegerField(choices=RATING_CHOICES, verbose_name=_('Rating'))
    content = models.TextField(verbose_name=_('Review Content'), default='')
    
    is_verified = models.BooleanField(default=False, verbose_name=_('Verified'))
    is_published = models.BooleanField(default=False, verbose_name=_('Published'))
    is_featured = models.BooleanField(default=False, verbose_name=_('Featured'))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated at'))
    
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name=_('IP Address'))
    
    def __str__(self):
        return f"{self.name} - {self.rating} stars"
    
    def notify_admin(self):
        """Отправляет уведомление администратору о новом отзыве"""
        subject = f'Новый отзыв на модерацию: {self.name} ({self.rating}★)'
        message = f"""
Новый отзыв требует модерации:

Имя: {self.name}
Email: {self.email}
Рейтинг: {self.rating}/5
Дата: {self.created_at}

Текст отзыва:
{self.content}

Ссылка на админку: {settings.ADMIN_URL}transactions/review/{self.id}/change/
"""
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=False,
            )
            return True
        except Exception as e:
            # В случае ошибки отправки
            print(f"Ошибка отправки уведомления: {e}")
            return False

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('review')
        verbose_name_plural = _('reviews')

# Сигнал для отправки уведомления при создании нового отзыва
@receiver(post_save, sender=Review)
def review_post_save(sender, instance, created, **kwargs):
    """Отправляет уведомление администратору при создании нового отзыва"""
    if created and not instance.is_published:
        instance.notify_admin()
