from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from django.utils import timezone
import uuid

# Типы валют
CURRENCY_TYPE_CHOICES = [
    ('fiat', _('Fiat')),
    ('crypto', _('Cryptocurrency')),
]

class Cryptocurrency(models.Model):
    """Модель для хранения информации о криптовалютах и фиатных валютах"""
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    symbol = models.CharField(max_length=20, unique=True, verbose_name=_('Symbol')) # Сделаем символ уникальным
    icon = models.ImageField(upload_to='crypto_icons/', blank=True, null=True, verbose_name=_('Icon'))
    
    currency_type = models.CharField(
        max_length=10,
        choices=CURRENCY_TYPE_CHOICES,
        default='crypto',
        verbose_name=_('Currency Type')
    )
    network = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Network')) # Например, ERC-20, TRC-20, Bitcoin
    
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    
    # Информация для API
    coingecko_id = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('CoinGecko ID'))
    # api_id = models.CharField(max_length=100, blank=True, null=True) # Это поле кажется дублирующим coingecko_id, можно убрать если не используется специфично
    
    # Минимальная и максимальная сумма для обмена (можно перенести в ExchangePair, если нужна гранулярность)
    min_exchange_amount = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0.0001'), verbose_name=_('Min Exchange Amount'))
    max_exchange_amount = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('10.0'), verbose_name=_('Max Exchange Amount'))
    
    # Комиссия платформы (в процентах) - лучше иметь глобальную настройку или в ExchangePair
    # platform_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.5'), verbose_name=_('Platform Fee Percentage'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.symbol})"
    
    class Meta:
        verbose_name = _('currency')
        verbose_name_plural = _('currencies')
        ordering = ['name']


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
    """Модель для хранения кошельков пользователей и системных кошельков"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallets',
        null=True, # Разрешаем Null для системных кошельков
        blank=True # Разрешаем Blank для системных кошельков
    )
    currency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, verbose_name=_('Currency')) # Переименовал crypto в currency для единообразия
    
    balance = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal('0.0'), verbose_name=_('Total Balance'))
    # address = models.CharField(max_length=255, blank=True, null=True) # Адрес пока не используем активно для внутренней логики
    
    available_balance = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal('0.0'), verbose_name=_('Available Balance'))
    locked_balance = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal('0.0'), verbose_name=_('Locked Balance')) # Для ордеров, инвестиций и т.д.
    
    is_system_wallet = models.BooleanField(default=False, verbose_name=_('System Wallet'))
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.is_system_wallet:
            return f"System Wallet - {self.currency.symbol}"
        if self.user:
            return f"{self.user.email} - {self.currency.symbol} Wallet" # Используем email, так как это USERNAME_FIELD
        return f"Orphaned Wallet - {self.currency.symbol}"


    def save(self, *args, **kwargs):
        # Убедимся, что системный кошелек не привязан к пользователю
        if self.is_system_wallet:
            self.user = None
        
        # При создании кошелька или если available_balance не был установлен вручную
        if self.pk is None or self.available_balance == Decimal('0.0') and self.locked_balance == Decimal('0.0'):
             self.available_balance = self.balance - self.locked_balance
        else:
            # Общий баланс всегда сумма доступного и заблокированного
            # Это условие может быть избыточным если available_balance и locked_balance управляются отдельно
            # и balance вычисляется как их сумма при чтении (через property например).
            # Для упрощения пока оставим как есть, но обычно меняется available/locked, а balance - их сумма.
            # Если же balance меняется напрямую, то available_balance должен быть пересчитан, если нет locked_balance.
            # Логика здесь может быть сложнее в зависимости от операций.
            # Пока предположим, что balance - это основное поле, а available_balance - это balance минус locked_balance.
            self.available_balance = self.balance - self.locked_balance
            if self.available_balance < 0:
                # Этого не должно происходить, нужна валидация или другая логика
                # Для примера, можно вызвать исключение или установить available_balance в 0
                # raise ValueError("Available balance cannot be negative.")
                self.available_balance = Decimal('0.0') 
                # И, возможно, скорректировать locked_balance или balance
                # self.balance = self.locked_balance # Если available_balance не может быть отрицательным

        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('user', 'currency', 'is_system_wallet') # Гарантируем уникальность кошелька для пользователя/системы и валюты
        verbose_name = _('wallet')
        verbose_name_plural = _('wallets')


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
    wallet = models.ForeignKey(
        UserWallet,
        on_delete=models.CASCADE,
        related_name='investments',
        null=True
    )
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
        return f"{self.user.username} - {self.amount} {self.wallet.currency.symbol} - {self.plan.name}"
    
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
    wallet = models.ForeignKey(
        UserWallet,
        on_delete=models.CASCADE,
        related_name='card_deposits',
        null=True
    )
    
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
        return f"Card deposit of {self.amount} {self.currency} by {self.user.username} ({self.status})"

    def save(self, *args, **kwargs):
        # Логика для автоматического зачисления средств при смене статуса на 'completed'
        if self.pk is not None:
            orig = CardDeposit.objects.get(pk=self.pk)
            if orig.status != 'completed' and self.status == 'completed':
                from .services import get_exchange_rates
                from decimal import Decimal

                self.completed_at = timezone.now()
                
                # Получаем целевой кошелек
                target_wallet = self.wallet
                target_crypto = target_wallet.currency
                
                # Получаем фиатную валюту из заявки
                try:
                    fiat_currency = Cryptocurrency.objects.get(symbol=self.currency, currency_type='fiat')
                except Cryptocurrency.DoesNotExist:
                    # Обработка случая, если фиатная валюта не найдена
                    # Здесь можно добавить логирование или другую логику
                    super().save(*args, **kwargs) # Сохраняем статус, но не проводим зачисление
                    return

                all_rates = get_exchange_rates()
                
                fiat_coingecko_id = fiat_currency.coingecko_id
                target_coingecko_id = target_crypto.coingecko_id
                
                fiat_rate_usd = all_rates.get(fiat_coingecko_id, {}).get('usd')
                target_rate_usd = all_rates.get(target_coingecko_id, {}).get('usd')

                if fiat_rate_usd and target_rate_usd:
                    try:
                        fiat_rate_usd_dec = Decimal(str(fiat_rate_usd))
                        target_rate_usd_dec = Decimal(str(target_rate_usd))
                        
                        exchange_rate = fiat_rate_usd_dec / target_rate_usd_dec
                        crypto_amount_to_add = self.amount * exchange_rate
                        
                        self.exchange_rate = exchange_rate
                        self.crypto_amount = crypto_amount_to_add
                        
                        target_wallet.balance += crypto_amount_to_add
                        target_wallet.save()
                        
                    except (ValueError, TypeError):
                        # Обработка ошибки конвертации
                        pass
        
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('card deposit')
        verbose_name_plural = _('card deposits')
