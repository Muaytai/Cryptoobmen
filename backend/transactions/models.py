from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from crypto.models import Cryptocurrency, UserWallet
import uuid


class Transaction(models.Model):
    """Основная модель для всех транзакций"""
    TYPE_CHOICES = (
        ('deposit', _('Deposit')),
        ('withdrawal', _('Withdrawal')),
        ('exchange', _('Exchange')),
        ('transfer', _('Transfer')),
        ('fee', _('Fee')),
    )
    
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    amount = models.DecimalField(max_digits=24, decimal_places=8)
    fee = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    
    crypto = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, related_name='transactions')
    
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Сетевая информация (для blockchain транзакций)
    tx_hash = models.CharField(max_length=255, blank=True, null=True)
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
    
    wallet = models.ForeignKey(UserWallet, on_delete=models.CASCADE, related_name='deposits')
    address = models.CharField(max_length=255)
    
    confirmed = models.BooleanField(default=False)
    confirmation_date = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"Deposit {self.transaction.amount} {self.wallet.crypto.symbol} to {self.address}"


class Withdrawal(models.Model):
    """Модель для вывода средств"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='withdrawals')
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='withdrawal')
    
    wallet = models.ForeignKey(UserWallet, on_delete=models.CASCADE, related_name='withdrawals')
    destination_address = models.CharField(max_length=255)
    
    # Двухфакторная авторизация для вывода
    is_2fa_confirmed = models.BooleanField(default=False)
    is_email_confirmed = models.BooleanField(default=False)
    
    # Статусы подтверждения
    confirmed_by_admin = models.BooleanField(default=False)
    rejected_reason = models.TextField(blank=True, null=True)
    
    # Время подтверждения
    confirmation_date = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"Withdrawal {self.transaction.amount} {self.wallet.crypto.symbol} to {self.destination_address}"
