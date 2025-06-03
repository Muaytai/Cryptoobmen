from django.contrib import admin
from .models import Cryptocurrency, CryptoPrice, ExchangePair, UserWallet, InvestmentPlan, UserInvestment, CardDeposit


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


@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'crypto', 'interest_rate', 'duration_value', 'duration_unit', 'min_investment', 'max_investment', 'is_active')
    list_filter = ('is_active', 'crypto__symbol', 'duration_unit')
    search_fields = ('name', 'description', 'crypto__name', 'crypto__symbol')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserInvestment)
class UserInvestmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'amount', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'plan__crypto__symbol', 'plan')
    search_fields = ('user__email', 'user__username', 'plan__name')
    readonly_fields = ('created_at', 'updated_at', 'start_date', 'end_date', 'expected_return', 'actual_return')


@admin.register(CardDeposit)
class CardDepositAdmin(admin.ModelAdmin):
    list_display = ('user', 'wallet_currency_display', 'amount', 'status', 'created_at')
    list_filter = ('status', 'wallet__currency__symbol', 'wallet__user__email')
    search_fields = ('user__email', 'user__username', 'card_last4')
    readonly_fields = ('created_at', 'updated_at', 'payment_id')

    def wallet_currency_display(self, obj):
        return obj.wallet.currency.symbol
    wallet_currency_display.short_description = 'Валюта кошелька'
