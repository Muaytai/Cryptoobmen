from django.contrib import admin
from django.conf import settings
from tronpy import Tron
from decimal import Decimal, getcontext
import logging
from .models import (
    Cryptocurrency, CryptoPrice, ExchangePair, UserWallet, 
    SystemWalletAddress, UserDepositMemo,
    BlockchainState, CommissionWallet, CommissionTransaction,
    GeneratedWallet
)
import csv
from django.http import HttpResponse


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
    list_display = ('user_display', 'currency', 'balance', 'available_balance', 'locked_balance', 'is_system_wallet', 'is_active', 'delete_button')
    list_filter = ('is_active', 'is_system_wallet', 'currency__symbol')
    search_fields = ('user__email', 'user__username', 'currency__name', 'currency__symbol')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['delete_selected_wallets']
    
    def has_delete_permission(self, request, obj=None):
        # Разрешаем удаление кошельков только суперпользователям
        return request.user.is_superuser
    
    def changelist_view(self, request, extra_context=None):
        """Сохраняем request для использования в других методах"""
        self._current_request = request
        return super().changelist_view(request, extra_context)
    
    def delete_button(self, obj):
        """Кнопка удаления для каждого кошелька"""
        from django.utils.html import format_html
        from django.urls import reverse
        
        # Проверяем, есть ли текущий запрос в контексте
        request = getattr(self, '_current_request', None)
        if request and self.has_delete_permission(request, obj):
            delete_url = reverse('admin:crypto_userwallet_delete', args=[obj.pk])
            # Формируем описание кошелька
            if obj.user:
                wallet_description = f"{obj.currency.symbol} для {obj.user.email}"
            else:
                wallet_description = f"Системный {obj.currency.symbol}"
            
            return format_html(
                '<a href="{}" onclick="return confirm(\'Вы уверены, что хотите удалить кошелек {}? Это действие необратимо!\')" '
                'style="background-color: #dc3545; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; font-size: 12px;">'
                '🗑️ Удалить</a>',
                delete_url, wallet_description
            )
        return '-'
    delete_button.short_description = 'Действия'
    delete_button.allow_tags = True
    
    def delete_selected_wallets(self, request, queryset):
        """Массовое удаление выбранных кошельков"""
        if not request.user.is_superuser:
            self.message_user(request, "Только суперпользователи могут удалять кошельки.", level='ERROR')
            return
        
        count = queryset.count()
        if count > 0:
            # Предупреждение о балансах
            wallets_with_balance = queryset.filter(balance__gt=0)
            if wallets_with_balance.exists():
                total_balance = sum(w.balance for w in wallets_with_balance)
                self.message_user(
                    request, 
                    f"ВНИМАНИЕ: {wallets_with_balance.count()} кошельков имеют баланс (общий: {total_balance}). "
                    f"Убедитесь, что это не приведет к потере средств!", 
                    level='WARNING'
                )
            
            deleted_objects = queryset.delete()
            self.message_user(request, f"Успешно удалено {count} кошельков")
        else:
            self.message_user(request, "Не выбрано ни одного кошелька для удаления.", level='WARNING')
    
    delete_selected_wallets.short_description = "🗑️ Удалить выбранные кошельки (ОСТОРОЖНО!)"

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


@admin.register(CommissionWallet)
class CommissionWalletAdmin(admin.ModelAdmin):
    list_display = ('currency', 'balance', 'is_active', 'updated_at')
    list_filter = ('is_active', 'currency__symbol')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CommissionTransaction)
class CommissionTransactionAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'commission_type', 'user', 'currency', 'amount', 'related_object_id')
    list_filter = ('commission_type', 'currency')
    search_fields = ('user__email', 'related_object_id')
    date_hierarchy = 'created_at'
    actions = ['export_as_csv']

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=commission_transactions.csv'
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])
        return response
    export_as_csv.short_description = "Экспортировать выбранные в CSV"


@admin.register(GeneratedWallet)
class GeneratedWalletAdmin(admin.ModelAdmin):
    list_display = ['address', 'currency', 'network', 'user', 'wallet_type', 'created_by', 'created_at', 'is_active']
    list_filter = ['currency', 'network', 'wallet_type', 'created_by', 'is_active', 'created_at']
    search_fields = ['address', 'user__email', 'created_by', 'notes']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('address', 'currency', 'network', 'wallet_type')
        }),
        ('Связи', {
            'fields': ('user',)
        }),
        ('Метаданные', {
            'fields': ('created_by', 'created_at', 'is_active')
        }),
        ('Приватный ключ', {
            'fields': ('encrypted_private_key',),
            'classes': ('collapse',),
            'description': 'ОСТОРОЖНО: Приватный ключ! Не показывать посторонним.'
        }),
        ('Дополнительно', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj:  # Если объект уже существует
            readonly_fields.extend(['address', 'currency', 'network', 'encrypted_private_key'])
        return readonly_fields
    
    actions = ['verify_key_address_match']
    
    def verify_key_address_match(self, request, queryset):
        """Проверяет соответствие приватного ключа и адреса для выбранных кошельков"""
        verified = 0
        mismatched = 0
        
        for wallet in queryset:
            if GeneratedWallet.verify_key_address_match(wallet.address, wallet.encrypted_private_key):
                verified += 1
            else:
                mismatched += 1
                
        self.message_user(
            request,
            f"Проверено кошельков: {verified + mismatched}. "
            f"Соответствуют: {verified}. Не соответствуют: {mismatched}."
        )
    verify_key_address_match.short_description = "Проверить соответствие ключ-адрес"
