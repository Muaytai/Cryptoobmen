from django.contrib import admin
from .models import Cryptocurrency, CryptoPrice, ExchangePair, UserWallet, InvestmentPlan, UserInvestment, CardDeposit


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
    list_display = ('user', 'crypto', 'balance', 'available_balance', 'locked_balance', 'is_active')
    list_filter = ('is_active', 'crypto')
    search_fields = ('user__email', 'user__username', 'crypto__name', 'crypto__symbol')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'crypto', 'interest_rate', 'duration_value', 'duration_unit', 'min_investment', 'max_investment', 'is_active')
    list_filter = ('is_active', 'crypto', 'duration_unit')
    search_fields = ('name', 'description', 'crypto__name', 'crypto__symbol')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserInvestment)
class UserInvestmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'amount', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'plan__crypto', 'plan')
    search_fields = ('user__email', 'user__username', 'plan__name')
    readonly_fields = ('created_at', 'updated_at', 'start_date', 'end_date', 'expected_return', 'actual_return')


@admin.register(CardDeposit)
class CardDepositAdmin(admin.ModelAdmin):
    list_display = ('user', 'wallet', 'amount', 'status', 'created_at')
    list_filter = ('status', 'wallet__crypto')
    search_fields = ('user__email', 'user__username', 'card_last4')
    readonly_fields = ('created_at', 'updated_at', 'payment_id')
