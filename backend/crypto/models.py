from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


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
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.crypto.symbol} Wallet"
    
    class Meta:
        unique_together = ('user', 'crypto')
        verbose_name = _('user wallet')
        verbose_name_plural = _('user wallets')
