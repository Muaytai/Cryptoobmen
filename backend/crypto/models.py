
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from django.utils import timezone
import uuid
import logging
from django.core.files.base import ContentFile
import base64
from .blockchain.factory import get_blockchain_service # Используем фабрику

logger = logging.getLogger(__name__)

# Типы валют
CURRENCY_TYPE_CHOICES = [
    ('fiat', _('Fiat')),
    ('crypto', _('Cryptocurrency')),
]

class Cryptocurrency(models.Model):
    """Модель для хранения информации о криптовалютах и фиатных валютах"""
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    symbol = models.CharField(max_length=20, verbose_name=_('Symbol')) # Убираем unique=True
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
    
    # Для токенов
    contract_address = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Contract Address'))
    decimals = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_('Decimals'))
    
    # Требуется ли Memo/Destination Tag для пополнения
    requires_memo = models.BooleanField(
        default=False,
        verbose_name=_('Requires Memo'),
        help_text=_('Check if this currency requires a Memo/Destination Tag for deposits.')
    )

    # Минимальная и максимальная сумма для обмена (можно перенести в ExchangePair, если нужна гранулярность)
    min_exchange_amount = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0.0001'), verbose_name=_('Min Exchange Amount'))
    max_exchange_amount = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('10.0'), verbose_name=_('Max Exchange Amount'))
    
    # Комиссия платформы (в процентах) - теперь активна
    fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.2'),  # 0.2 % – «невысокая» по сравнению с рынком
        verbose_name=_('Platform Fee Percentage'),
        help_text=_('Default platform commission in percent (0-100)')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.network:
            return f"{self.name} ({self.symbol} - {self.network})"
        return f"{self.name} ({self.symbol})"
    
    class Meta:
        verbose_name = _('currency')
        verbose_name_plural = _('currencies')
        ordering = ['name']
        unique_together = ['symbol', 'network']  # Делаем уникальной комбинацию символа и сети


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
    
    deposit_address = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Deposit Address'))

    is_system_wallet = models.BooleanField(default=False, verbose_name=_('System Wallet'))

    # Храним приватный ключ для системного кошелька в зашифрованном виде (Fernet)
    encrypted_private_key = models.TextField(blank=True, null=True, verbose_name=_('Encrypted Private Key'))
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
        # МОНИТОРИНГ: Отслеживаем ВСЕ изменения deposit_address
        if self.pk is not None:  # Существующий объект
            try:
                old_wallet = UserWallet.objects.get(pk=self.pk)
                if old_wallet.deposit_address != self.deposit_address:
                    import traceback
                    stack_trace = ''.join(traceback.format_stack()[-10:])  # Ещё больше кадров
                    
                    change_type = "UNKNOWN"
                    if old_wallet.deposit_address and not self.deposit_address:
                        change_type = "CLEARED (обнулён)"
                    elif not old_wallet.deposit_address and self.deposit_address:
                        change_type = "GENERATED (создан)"
                    elif old_wallet.deposit_address and self.deposit_address:
                        change_type = "REPLACED (заменён)"
                    
                    logger.error(f"🚨 DEPOSIT ADDRESS {change_type}!")
                    logger.error(f"   User: {self.user.id if self.user else 'None'} ({self.user.email if self.user else 'None'})")
                    logger.error(f"   Currency: {self.currency.symbol}")
                    logger.error(f"   OLD: '{old_wallet.deposit_address}'")
                    logger.error(f"   NEW: '{self.deposit_address}'")
                    logger.error(f"   Type: {change_type}")
                    logger.error(f"   Call stack:\n{stack_trace}")
                    
                    # Также логируем в файл для надёжности
                    try:
                        with open('/tmp/address_changes.log', 'a') as f:
                            from datetime import datetime
                            f.write(f"\n{datetime.now()}: {change_type}\n")
                            f.write(f"User {self.user.id if self.user else 'None'}: {old_wallet.deposit_address} -> {self.deposit_address}\n")
                            f.write(f"Stack:\n{stack_trace}\n{'='*50}\n")
                    except:
                        pass
                        
            except UserWallet.DoesNotExist:
                pass  # Новый объект, это нормально
        
        # Убедимся, что системный кошелек не привязан к пользователю
        if self.is_system_wallet:
            self.user = None

        # ОТКЛЮЧЕНО: Автоматическая генерация адресов в модели
        # Адреса теперь генерируются только через DepositService или после консолидации
        # if self.currency.currency_type == 'crypto' and not self.deposit_address and not self.is_system_wallet:
        #     import traceback
        #     stack_trace = ''.join(traceback.format_stack()[-5:])  # Последние 5 кадров
        #     logger.warning(f"🚨 AUTO-GENERATING ADDRESS for {self.currency.symbol} user {self.user.email if self.user else 'None'}")
        #     logger.warning(f"🚨 Call stack:\n{stack_trace}")
        #     try:
        #         # Используем фабрику для получения нужного сервиса
        #         service = get_blockchain_service(self.currency.network)
        #         # create_new_address теперь может возвращать кортеж (адрес, приватный ключ)
        #         new_address, private_key = service.create_new_address()
        #         self.deposit_address = new_address
        #         # В проде здесь должно быть шифрование
        #         self.encrypted_private_key = private_key 
        #         logger.warning(f"🚨 Generated new {self.currency.symbol} address {new_address} for user {self.user.email if self.user else 'None'}")
        #     except Exception as e:
        #         logger.error(f"Could not generate address for {self.currency.symbol}: {e}")
        pass  # Заглушка для правильного синтаксиса

        # При создании кошелька или если available_balance не был установлен вручную
        if self.pk is None or self.available_balance == Decimal('0.0') and self.locked_balance == Decimal('0.0'):
             self.available_balance = self.balance - self.locked_balance
        else:
            # Available balance не может быть больше общего баланса
            self.available_balance = self.balance - self.locked_balance
            if self.available_balance < 0:
                self.available_balance = Decimal('0.0')
            elif self.available_balance > self.balance:
                self.available_balance = self.balance

        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('user', 'currency', 'is_system_wallet') # Гарантируем уникальность кошелька для пользователя/системы и валюты
        verbose_name = _('wallet')
        verbose_name_plural = _('wallets')




class SystemWalletAddress(models.Model):
    """
    Адреса системных кошельков для пополнения.
    Один адрес на каждую связку "валюта + сеть".
    """
    currency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, related_name='system_addresses')
    network = models.CharField(max_length=50, verbose_name=_('Network'))
    address = models.CharField(max_length=255, verbose_name=_('Address'))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"System Address: {self.currency.symbol} ({self.network})"

    class Meta:
        unique_together = ('currency', 'network')
        verbose_name = _('System Wallet Address')
        verbose_name_plural = _('System Wallet Addresses')


class UserDepositMemo(models.Model):
    """
    Уникальные Memo, выдаваемые пользователям для пополнения системных кошельков.
    """
    STATUS_CHOICES = (
        ('waiting', _('Waiting for deposit')),
        ('used', _('Used')),
        ('expired', _('Expired')),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deposit_memos')
    currency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE)
    network = models.CharField(max_length=50, verbose_name=_('Network'))
    memo = models.CharField(max_length=128, unique=True, verbose_name=_('Memo/Destination Tag'))
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(verbose_name=_('Expires At'))

    def __str__(self):
        return f"Memo {self.memo} for {self.user.email} - {self.currency.symbol} ({self.network})"

    class Meta:
        verbose_name = _('User Deposit Memo')
        verbose_name_plural = _('User Deposit Memos')


class BlockchainState(models.Model):
    """
    Хранит состояние сканера блокчейна, например, последний обработанный блок.
    """
    blockchain = models.CharField(max_length=50, unique=True, primary_key=True, verbose_name=_('Blockchain/Network'))
    last_processed_block = models.BigIntegerField(default=0, verbose_name=_('Last Processed Block'))
    updated_at = models.DateTimeField(auto_now=True)


class ExchangeOrder(models.Model):
    """Ордер на обмен одной криптовалюты на другую внутри платформы."""

    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('executed', _('Executed')),
        ('canceled', _('Canceled')),
        ('failed', _('Failed')),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exchange_orders')

    from_currency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, related_name='exchange_orders_from')
    to_currency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, related_name='exchange_orders_to')

    from_amount = models.DecimalField(max_digits=28, decimal_places=8)
    to_amount = models.DecimalField(max_digits=28, decimal_places=8)

    rate = models.DecimalField(max_digits=28, decimal_places=12, help_text=_('Exchange rate applied'))

    fee_percent = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0'), help_text=_('Fee percent taken'))
    fee_amount = models.DecimalField(max_digits=28, decimal_places=8, default=Decimal('0'))

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    executed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('exchange order')
        verbose_name_plural = _('exchange orders')

    def __str__(self):
        return f"{self.from_amount} {self.from_currency.symbol} -> {self.to_currency.symbol} ({self.status})"


# -------------------------------------------------------------
#  CommissionWallet – внутренний кошелёк для накопления дохода
# -------------------------------------------------------------
# Отдельная таблица, чтобы не усложнять существующую модель UserWallet
# дополнительными флагами. Для каждой активной валюты хранится
# агрегированный баланс комиссии (profit) платформы. Видно только админам.


class CommissionWallet(models.Model):
    """Внутренний кошелёк для накопления комиссии платформы по каждой валюте."""

    currency = models.ForeignKey(
        Cryptocurrency,
        on_delete=models.CASCADE,
        related_name='commission_wallets',
        verbose_name=_('Currency'),
    )

    balance = models.DecimalField(
        max_digits=24,
        decimal_places=8,
        default=Decimal('0.0'),
        verbose_name=_('Commission Balance'),
    )

    is_active = models.BooleanField(default=True, verbose_name=_('Active'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('currency',)
        verbose_name = _('commission wallet')
        verbose_name_plural = _('commission wallets')

    def __str__(self):
        return f"Commission Wallet – {self.currency.symbol}"  


# -------------------------------------------------------------
#  CommissionTransaction – история начисления комиссий
# -------------------------------------------------------------
class CommissionTransaction(models.Model):
    """История начисления комиссий платформы (exchange, withdraw и др.)."""
    COMMISSION_TYPE_CHOICES = [
        ('exchange', 'Обмен'),
        ('withdraw', 'Вывод'),
    ]
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    currency = models.ForeignKey('Cryptocurrency', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=24, decimal_places=8)
    commission_type = models.CharField(max_length=16, choices=COMMISSION_TYPE_CHOICES)
    related_object_id = models.CharField(max_length=64, blank=True, null=True, help_text='ID связанной операции (например, ExchangeOrder или Withdrawal)')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'commission transaction'
        verbose_name_plural = 'commission transactions'

    def __str__(self):
        return f"{self.get_commission_type_display()} {self.amount} {self.currency.symbol} ({self.created_at:%Y-%m-%d %H:%M})"  


# --- Фикстура для автозаполнения популярных валют и сетей ---
def create_default_cryptocurrencies():
    # Примеры: BTC, ETH, USDT-ERC20, USDT-TRC20, BNB, XRP, LTC, SOL, MATIC
    default_cryptos = [
        {"name": "Bitcoin", "symbol": "BTC", "network": "BTC", "decimals": 8, "requires_memo": False, "icon_b64": None},
        {"name": "Ethereum", "symbol": "ETH", "network": "ERC20", "decimals": 18, "requires_memo": False, "icon_b64": None},
        {"name": "Tether USD", "symbol": "USDT", "network": "ERC20", "decimals": 6, "requires_memo": False, "icon_b64": None},
        {"name": "Tether USD", "symbol": "USDT", "network": "TRC20", "decimals": 6, "requires_memo": False, "icon_b64": None},
        {"name": "Tron", "symbol": "TRX", "network": "TRC20", "decimals": 6, "requires_memo": False, "icon_b64": None},
        {"name": "Binance Coin", "symbol": "BNB", "network": "BEP20", "decimals": 18, "requires_memo": True, "icon_b64": None},
        {"name": "Ripple", "symbol": "XRP", "network": "XRP", "decimals": 6, "requires_memo": True, "icon_b64": None},
        {"name": "Litecoin", "symbol": "LTC", "network": "LTC", "decimals": 8, "requires_memo": False, "icon_b64": None},
        {"name": "Solana", "symbol": "SOL", "network": "SOL", "decimals": 9, "requires_memo": False, "icon_b64": None},
        {"name": "Polygon", "symbol": "POL", "network": "Polygon", "decimals": 18, "requires_memo": False, "icon_b64": None},
    ]
    for crypto_data in default_cryptos:
        obj, created = Cryptocurrency.objects.get_or_create(
            symbol=crypto_data["symbol"], 
            network=crypto_data["network"], 
            defaults={
                "name": crypto_data["name"],
                "decimals": crypto_data["decimals"],
                "requires_memo": crypto_data["requires_memo"]
            }
        )
        if created:
            if crypto_data["icon_b64"]:
                obj.icon.save(f"{crypto_data['symbol']}.png", ContentFile(base64.b64decode(crypto_data["icon_b64"])), save=True)
        else:
            # Update existing records if needed
            obj.decimals = crypto_data["decimals"]
            obj.requires_memo = crypto_data["requires_memo"]
        
        obj.is_active = True
        obj.save()

# Вызов при миграции или через shell


class GeneratedWallet(models.Model):
    """
    Отслеживает все сгенерированные кошельки для предотвращения потери соответствия ключ-адрес
    """
    address = models.CharField(max_length=255, unique=True, verbose_name=_('Wallet Address'), db_index=True)
    encrypted_private_key = models.TextField(verbose_name=_('Encrypted Private Key'))
    currency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, verbose_name=_('Currency'))
    network = models.CharField(max_length=50, verbose_name=_('Network'))
    
    # Связь с пользователем (может быть None для системных кошельков)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('User'))
    
    # Тип кошелька
    WALLET_TYPE_CHOICES = [
        ('user', _('User Wallet')),
        ('system', _('System Wallet')),
        ('test', _('Test Wallet')),
    ]
    wallet_type = models.CharField(max_length=10, choices=WALLET_TYPE_CHOICES, default='user', verbose_name=_('Wallet Type'))
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    created_by = models.CharField(max_length=100, blank=True, verbose_name=_('Created By'))  # Функция/модуль создания
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))
    
    # Дополнительная информация
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    
    class Meta:
        verbose_name = _('Generated Wallet')
        verbose_name_plural = _('Generated Wallets')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['address']),
            models.Index(fields=['currency', 'network']),
            models.Index(fields=['user', 'wallet_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        user_info = f"User {self.user.id}" if self.user else "System"
        return f"{self.address} ({self.currency.symbol}/{self.network}) - {user_info}"
    
    @classmethod
    def record_generated_wallet(cls, address: str, private_key: str, currency, network: str, 
                              user=None, wallet_type: str = 'user', created_by: str = '', notes: str = ''):
        """
        Записывает сгенерированный кошелек в БД
        """
        return cls.objects.create(
            address=address,
            encrypted_private_key=private_key,
            currency=currency,
            network=network,
            user=user,
            wallet_type=wallet_type,
            created_by=created_by,
            notes=notes
        )
    
    @classmethod
    def get_wallet_by_address(cls, address: str):
        """
        Получить информацию о кошельке по адресу
        """
        try:
            return cls.objects.get(address=address)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def verify_key_address_match(cls, address: str, private_key: str) -> bool:
        """
        Проверяет соответствие приватного ключа и адреса
        """
        try:
            from eth_account import Account
            account = Account.from_key(private_key)
            return account.address.lower() == address.lower()
        except Exception:
            return False

