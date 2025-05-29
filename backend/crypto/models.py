from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from django.utils import timezone
import uuid


class Cryptocurrency(models.Model):
    """Модель для хранения информации о криптовалютах"""
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20)
    icon = models.ImageField(upload_to='crypto_icons/', blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    
    # Информация для API
    coingecko_id = models.CharField(max_length=100, blank=True, null=True)
    api_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Минимальная и максимальная сумма для обмена
    min_amount = models.DecimalField(max_digits=18, decimal_places=8, default=0.0001)
    max_amount = models.DecimalField(max_digits=18, decimal_places=8, default=10)
    
    # Комиссия платформы (в процентах)
    fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.5)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.symbol})"
    
    class Meta:
        verbose_name = _('cryptocurrency')
        verbose_name_plural = _('cryptocurrencies')


class CryptoPrice(models.Model):
    """Модель для хранения истории цен криптовалют"""
    crypto = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, related_name='prices')
    price_usd = models.DecimalField(max_digits=18, decimal_places=8)
    price_btc = models.DecimalField(max_digits=18, decimal_places=8, blank=True, null=True)
    price_eth = models.DecimalField(max_digits=18, decimal_places=8, blank=True, null=True)
    
    market_cap = models.DecimalField(max_digits=24, decimal_places=2, blank=True, null=True)
    volume_24h = models.DecimalField(max_digits=24, decimal_places=2, blank=True, null=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.crypto.symbol} - ${self.price_usd} at {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']


class ExchangePair(models.Model):
    """Модель для хранения доступных пар для обмена"""
    from_crypto = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, related_name='from_pairs')
    to_crypto = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, related_name='to_pairs')
    
    is_active = models.BooleanField(default=True)
    
    # Дополнительная комиссия для конкретной пары (если отличается от стандартной)
    custom_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    
    # Минимальная и максимальная сумма для обмена конкретной пары
    min_from_amount = models.DecimalField(max_digits=18, decimal_places=8, blank=True, null=True)
    max_from_amount = models.DecimalField(max_digits=18, decimal_places=8, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.from_crypto.symbol} -> {self.to_crypto.symbol}"
    
    class Meta:
        unique_together = ('from_crypto', 'to_crypto')
        verbose_name = _('exchange pair')
        verbose_name_plural = _('exchange pairs')


class UserWallet(models.Model):
    """Модель для хранения кошельков пользователей"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallets')
    crypto = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE)
    
    balance = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    address = models.CharField(max_length=255, blank=True, null=True)
    
    # Для отслеживания доступных и замороженных средств (в инвестициях)
    available_balance = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    locked_balance = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.crypto.symbol} Wallet"
    
    def save(self, *args, **kwargs):
        # При создании кошелька available_balance = balance
        if not self.pk:
            self.available_balance = self.balance
        # При обновлении проверяем, что сумма available + locked = balance
        else:
            self.balance = self.available_balance + self.locked_balance
        super().save(*args, **kwargs)
    
    class Meta:
        unique_together = ('user', 'crypto')
        verbose_name = _('user wallet')
        verbose_name_plural = _('user wallets')


class InvestmentPlan(models.Model):
    """Модель для инвестиционных планов"""
    DURATION_CHOICES = (
        ('day', _('Day')),
        ('week', _('Week')),
        ('month', _('Month')),
        ('year', _('Year')),
    )
    
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    description = models.TextField(verbose_name=_('Description'))
    
    crypto = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, related_name='investment_plans')
    
    # Процент доходности
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_('Interest Rate (%)'))
    
    # Продолжительность инвестиции
    duration_value = models.PositiveIntegerField(default=1, verbose_name=_('Duration Value'))
    duration_unit = models.CharField(max_length=10, choices=DURATION_CHOICES, default='month', verbose_name=_('Duration Unit'))
    
    # Минимальная и максимальная сумма инвестиции
    min_investment = models.DecimalField(max_digits=18, decimal_places=8, verbose_name=_('Minimum Investment'))
    max_investment = models.DecimalField(max_digits=18, decimal_places=8, verbose_name=_('Maximum Investment'))
    
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    
    # Дополнительные настройки
    early_withdrawal_allowed = models.BooleanField(default=False, verbose_name=_('Early Withdrawal Allowed'))
    early_withdrawal_fee = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name=_('Early Withdrawal Fee (%)'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.interest_rate}% за {self.duration_value} {self.get_duration_unit_display()}"
    
    def get_duration_in_days(self):
        """Возвращает продолжительность в днях"""
        if self.duration_unit == 'day':
            return self.duration_value
        elif self.duration_unit == 'week':
            return self.duration_value * 7
        elif self.duration_unit == 'month':
            return self.duration_value * 30
        elif self.duration_unit == 'year':
            return self.duration_value * 365
        return 0
    
    class Meta:
        verbose_name = _('investment plan')
        verbose_name_plural = _('investment plans')


class UserInvestment(models.Model):
    """Модель для инвестиций пользователей"""
    STATUS_CHOICES = (
        ('active', _('Active')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('withdrawn', _('Withdrawn Early')),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='investments')
    wallet = models.ForeignKey(UserWallet, on_delete=models.CASCADE, related_name='investments')
    plan = models.ForeignKey(InvestmentPlan, on_delete=models.CASCADE, related_name='user_investments')
    
    investment_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Сумма инвестиции и ожидаемая прибыль
    amount = models.DecimalField(max_digits=24, decimal_places=8, verbose_name=_('Investment Amount'))
    expected_return = models.DecimalField(max_digits=24, decimal_places=8, verbose_name=_('Expected Return'))
    
    # Даты начала и окончания
    start_date = models.DateTimeField(default=timezone.now, verbose_name=_('Start Date'))
    end_date = models.DateTimeField(verbose_name=_('End Date'))
    
    # Статус инвестиции
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name=_('Status'))
    
    # Фактический возврат (может отличаться от ожидаемого при досрочном выводе)
    actual_return = models.DecimalField(max_digits=24, decimal_places=8, null=True, blank=True, verbose_name=_('Actual Return'))
    completed_date = models.DateTimeField(null=True, blank=True, verbose_name=_('Completion Date'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.amount} {self.wallet.crypto.symbol} - {self.plan.name}"
    
    def save(self, *args, **kwargs):
        # Если это новая инвестиция
        if not self.pk:
            # Рассчитываем ожидаемый доход
            interest_decimal = self.plan.interest_rate / Decimal('100.0')
            self.expected_return = self.amount * interest_decimal
            
            # Устанавливаем дату окончания
            days = self.plan.get_duration_in_days()
            self.end_date = self.start_date + timezone.timedelta(days=days)
        
        super().save(*args, **kwargs)
    
    def get_progress_percentage(self):
        """Возвращает процент выполнения инвестиции"""
        if self.status != 'active':
            return 100
        
        total_duration = (self.end_date - self.start_date).total_seconds()
        elapsed_duration = (timezone.now() - self.start_date).total_seconds()
        
        if total_duration <= 0:
            return 0
        
        progress = (elapsed_duration / total_duration) * 100
        return min(max(progress, 0), 100)  # Ограничиваем значение от 0 до 100
    
    class Meta:
        verbose_name = _('user investment')
        verbose_name_plural = _('user investments')


class CardDeposit(models.Model):
    """Модель для пополнения кошелька с банковской карты"""
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='card_deposits')
    wallet = models.ForeignKey(UserWallet, on_delete=models.CASCADE, related_name='card_deposits')
    
    deposit_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Информация о платеже
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Amount'))
    currency = models.CharField(max_length=3, default='RUB', verbose_name=_('Currency'))
    
    # Информация о карте (храним только маскированный номер)
    card_last4 = models.CharField(max_length=4, blank=True, null=True, verbose_name=_('Last 4 digits'))
    card_brand = models.CharField(max_length=20, blank=True, null=True, verbose_name=_('Card Brand'))
    
    # Информация о статусе
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name=_('Status'))
    payment_id = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Payment ID'))
    
    # Дополнительная информация
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_('Fee'))
    crypto_amount = models.DecimalField(max_digits=24, decimal_places=8, blank=True, null=True, verbose_name=_('Crypto Amount'))
    exchange_rate = models.DecimalField(max_digits=24, decimal_places=8, blank=True, null=True, verbose_name=_('Exchange Rate'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name=_('Completed At'))
    
    def __str__(self):
        return f"{self.user.username} - {self.amount} {self.currency} to {self.wallet.crypto.symbol}"
    
    class Meta:
        verbose_name = _('card deposit')
        verbose_name_plural = _('card deposits')
