from django.contrib import admin
from .models import Transaction, Exchange, Deposit, Withdrawal


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'type', 'status', 'amount', 'crypto', 'timestamp')
    list_filter = ('type', 'status', 'crypto')
    search_fields = ('transaction_id', 'user__email', 'user__username', 'tx_hash')
    readonly_fields = ('transaction_id', 'timestamp', 'updated_at')
    date_hierarchy = 'timestamp'
    
    def has_delete_permission(self, request, obj=None):
        # Запрещаем удаление транзакций через админку
        return False


@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'user', 'from_crypto', 'to_crypto', 'from_amount', 'to_amount', 'timestamp')
    list_filter = ('from_crypto', 'to_crypto')
    search_fields = ('user__email', 'user__username', 'transaction__transaction_id')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'user', 'wallet', 'address', 'confirmed')
    list_filter = ('confirmed', 'wallet__crypto')
    search_fields = ('user__email', 'user__username', 'transaction__transaction_id', 'address')
    readonly_fields = ('transaction', 'user', 'wallet', 'address')
    
    def has_add_permission(self, request):
        return False


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'user', 'wallet', 'destination_address', 'is_2fa_confirmed', 'is_email_confirmed', 'confirmed_by_admin')
    list_filter = ('is_2fa_confirmed', 'is_email_confirmed', 'confirmed_by_admin', 'wallet__crypto')
    search_fields = ('user__email', 'user__username', 'transaction__transaction_id', 'destination_address')
    readonly_fields = ('transaction', 'user', 'wallet', 'destination_address', 'is_2fa_confirmed', 'is_email_confirmed')
    
    def has_add_permission(self, request):
        return False
