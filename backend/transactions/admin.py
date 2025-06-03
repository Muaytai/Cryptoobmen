from django.contrib import admin
from .models import Transaction, Exchange, Deposit, Withdrawal, Review
from django.utils.html import format_html


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'type', 'status', 'amount', 'crypto', 'timestamp')
    list_filter = ('type', 'status', 'crypto__symbol')
    search_fields = ('transaction_id', 'user__email', 'user__username', 'tx_hash', 'crypto__symbol')
    readonly_fields = ('transaction_id', 'timestamp', 'updated_at')
    date_hierarchy = 'timestamp'
    
    def has_delete_permission(self, request, obj=None):
        # Запрещаем удаление транзакций через админку
        return False


@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'user', 'from_crypto', 'to_crypto', 'from_amount', 'to_amount', 'timestamp')
    list_filter = ('from_crypto__symbol', 'to_crypto__symbol')
    search_fields = ('user__email', 'user__username', 'transaction__transaction_id', 'from_crypto__symbol', 'to_crypto__symbol')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'user', 'wallet_currency_display', 'address', 'confirmed')
    list_filter = ('confirmed', 'wallet__currency__symbol')
    search_fields = ('user__email', 'user__username', 'transaction__transaction_id', 'address', 'wallet__currency__symbol')
    readonly_fields = ('transaction', 'user', 'wallet', 'address')
    
    def wallet_currency_display(self, obj):
        if obj.wallet:
            return obj.wallet.currency.symbol
        return "-"
    wallet_currency_display.short_description = 'Валюта кошелька'
    
    def has_add_permission(self, request):
        return False


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'user', 'wallet_currency_display', 'destination_address', 'is_2fa_confirmed', 'is_email_confirmed', 'confirmed_by_admin')
    list_filter = ('is_2fa_confirmed', 'is_email_confirmed', 'confirmed_by_admin', 'wallet__currency__symbol')
    search_fields = ('user__email', 'user__username', 'transaction__transaction_id', 'destination_address', 'wallet__currency__symbol')
    readonly_fields = ('transaction', 'user', 'wallet', 'destination_address', 'is_2fa_confirmed', 'is_email_confirmed')
    
    def wallet_currency_display(self, obj):
        if obj.wallet:
            return obj.wallet.currency.symbol
        return "-"
    wallet_currency_display.short_description = 'Валюта кошелька'

    def has_add_permission(self, request):
        return False


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'display_rating', 'created_at', 'short_content', 
                    'is_verified', 'is_published', 'is_featured', 'moderation_status')
    list_filter = ('is_published', 'is_verified', 'is_featured', 'rating', 'created_at')
    search_fields = ('name', 'email', 'content')
    readonly_fields = ('created_at',)
    actions = ['make_published', 'make_unpublished', 'mark_verified', 'mark_featured']
    date_hierarchy = 'created_at'
    list_per_page = 20
    
    fieldsets = (
        ('Информация о пользователе', {
            'fields': ('name', 'email')
        }),
        ('Содержание отзыва', {
            'fields': ('rating', 'content', 'created_at')
        }),
        ('Статус модерации', {
            'fields': ('is_published', 'is_verified', 'is_featured'),
            'description': 'Управление видимостью и статусом отзыва'
        }),
    )
    
    def short_content(self, obj):
        """Сокращенное содержание отзыва для отображения в списке"""
        max_length = 50
        return obj.content[:max_length] + '...' if len(obj.content) > max_length else obj.content
    short_content.short_description = 'Текст отзыва'
    
    def display_rating(self, obj):
        """Визуализация рейтинга звездочками"""
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: #FFD700;">{}</span>', stars)
    display_rating.short_description = 'Рейтинг'
    
    def moderation_status(self, obj):
        """Статус модерации с цветовым индикатором"""
        if not obj.is_published:
            return format_html('<span style="color: red; font-weight: bold;">⚠️ Требует модерации</span>')
        elif obj.is_featured:
            return format_html('<span style="color: green; font-weight: bold;">✓ Опубликован (избранный)</span>')
        elif obj.is_published:
            return format_html('<span style="color: green;">✓ Опубликован</span>')
    moderation_status.short_description = 'Статус'
    
    def make_published(self, request, queryset):
        """Опубликовать выбранные отзывы"""
        queryset.update(is_published=True)
    make_published.short_description = "Опубликовать выбранные отзывы"
    
    def make_unpublished(self, request, queryset):
        """Снять с публикации выбранные отзывы"""
        queryset.update(is_published=False)
    make_unpublished.short_description = "Снять с публикации выбранные отзывы"
    
    def mark_verified(self, request, queryset):
        """Отметить отзывы как проверенные"""
        queryset.update(is_verified=True)
    mark_verified.short_description = "Отметить как проверенные"
    
    def mark_featured(self, request, queryset):
        """Добавить отзывы в избранное"""
        queryset.update(is_featured=True, is_published=True, is_verified=True)
    mark_featured.short_description = "Добавить в избранное"
