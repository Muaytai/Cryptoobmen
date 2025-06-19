from django.contrib import admin
from django.conf import settings
from tronpy import Tron
from decimal import Decimal, getcontext
import logging
from .models import (
    Cryptocurrency, CryptoPrice, ExchangePair, UserWallet, 
    SystemWalletAddress, UserDepositMemo,
    BlockchainState
)


@admin.register(Cryptocurrency)
class CryptocurrencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'currency_type', 'network', 'is_active', 'min_exchange_amount', 'max_exchange_amount')
    list_filter = ('is_active', 'currency_type', 'network')
    search_fields = ('name', 'symbol', 'network')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CryptoPrice)
class CryptoPriceAdmin(admin.ModelAdmin):
    list_display = ('crypto', 'price_usd', 'price_btc', 'timestamp')
    list_filter = ('crypto__symbol',)
    search_fields = ('crypto__name', 'crypto__symbol')
    readonly_fields = ('timestamp',)
    
    def has_change_permission(self, request, obj=None):
        # Запрещаем изменение истории цен
        return False


@admin.register(ExchangePair)
class ExchangePairAdmin(admin.ModelAdmin):
    list_display = ('from_crypto', 'to_crypto', 'is_active', 'custom_fee_percentage')
    list_filter = ('is_active', 'from_crypto__symbol', 'to_crypto__symbol')
    search_fields = ('from_crypto__name', 'to_crypto__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserWallet)
class UserWalletAdmin(admin.ModelAdmin):
    list_display = ('user_display', 'currency', 'balance', 'available_balance', 'locked_balance', 'is_system_wallet', 'is_active')
    list_filter = ('is_active', 'is_system_wallet', 'currency__symbol')
    search_fields = ('user__email', 'user__username', 'currency__name', 'currency__symbol')
    readonly_fields = ('created_at', 'updated_at')

    def user_display(self, obj):
        if obj.user:
            return obj.user.email
        return "Системный кошелек"
    user_display.short_description = 'Пользователь / Система'





@admin.register(SystemWalletAddress)
class SystemWalletAddressAdmin(admin.ModelAdmin):
    list_display = ('currency', 'network', 'address', 'display_balance', 'created_at')
    list_filter = ('currency', 'network')
    search_fields = ('address', 'currency__symbol', 'network')
    readonly_fields = ('created_at', 'display_balance')

    getcontext().prec = 28
    
    logger = logging.getLogger(__name__)

    def display_balance(self, obj):
        """Запрашивает и отображает баланс токена для данного адреса кошелька."""

        self.logger.info(f"Attempting to fetch balance for {obj.address} ({obj.currency.symbol})")
        self.logger.info(f"  - Network: {obj.network}")
        self.logger.info(f"  - Contract Address: {obj.currency.contract_address}")
        self.logger.info(f"  - Decimals: {obj.currency.decimals}")
        
        # Проверяем, что это TRC20 токен и у него есть адрес контракта
        if obj.network.upper() != 'TRC20' or not obj.currency.contract_address or not obj.currency.decimals:
            self.logger.warning("  - Conditions not met, returning 'N/A'.")
            return "N/A"

        try:
            client = Tron(network='nile', conf={'api_key': settings.TRONGRID_API_KEY})
            contract = client.get_contract(obj.currency.contract_address)

            raw_balance = contract.functions.balanceOf(obj.address)

            decimals = obj.currency.decimals
            balance = Decimal(raw_balance) / Decimal(10**decimals)

            return f"{balance.normalize():f} {obj.currency.symbol}"

        except Exception as e:
            # Логируем ошибку, чтобы видеть ее в консоли сервера
            self.logger.error(f"Could not fetch balance for {obj.address}: {e}", exc_info=True)
            return f"API Error"

    display_balance.short_description = 'Real-time Balance'


@admin.register(UserDepositMemo)
class UserDepositMemoAdmin(admin.ModelAdmin):
    list_display = ('user', 'currency', 'network', 'memo', 'status', 'created_at', 'expires_at')
    list_filter = ('status', 'currency', 'network')
    search_fields = ('user__email', 'memo')
    readonly_fields = ('user', 'currency', 'network', 'memo', 'created_at', 'expires_at')


@admin.register(BlockchainState)
class BlockchainStateAdmin(admin.ModelAdmin):
    list_display = ('blockchain', 'last_processed_block', 'updated_at')
    readonly_fields = ('updated_at',)
