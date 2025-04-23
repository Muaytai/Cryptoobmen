from django.contrib import admin
from .models import Cryptocurrency, CryptoPrice, ExchangePair, UserWallet


@admin.register(Cryptocurrency)
class CryptocurrencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'is_active', 'min_amount', 'max_amount', 'fee_percentage')
    list_filter = ('is_active',)
    search_fields = ('name', 'symbol')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CryptoPrice)
class CryptoPriceAdmin(admin.ModelAdmin):
    list_display = ('crypto', 'price_usd', 'price_btc', 'timestamp')
    list_filter = ('crypto',)
    search_fields = ('crypto__name', 'crypto__symbol')
    readonly_fields = ('timestamp',)
    
    def has_change_permission(self, request, obj=None):
        # Запрещаем изменение истории цен
        return False


@admin.register(ExchangePair)
class ExchangePairAdmin(admin.ModelAdmin):
    list_display = ('from_crypto', 'to_crypto', 'is_active', 'custom_fee_percentage')
    list_filter = ('is_active', 'from_crypto', 'to_crypto')
    search_fields = ('from_crypto__name', 'to_crypto__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserWallet)
class UserWalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'crypto', 'balance', 'is_active')
    list_filter = ('is_active', 'crypto')
    search_fields = ('user__email', 'user__username', 'crypto__name', 'crypto__symbol')
    readonly_fields = ('created_at', 'updated_at')
