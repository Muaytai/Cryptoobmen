from django import forms
from django.contrib import admin
from .models import Transaction, Exchange, Deposit, Withdrawal, Review
from django.utils.html import format_html
from django.middleware.csrf import get_token


class StatusChangeForm(forms.Form):
    """Форма для изменения статуса транзакции"""
    STATUS_CHOICES = Transaction.STATUS_CHOICES
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'type', 'status', 'amount', 'crypto', 'timestamp')
    list_filter = ('type', 'status', 'crypto__symbol')
    search_fields = ('transaction_id', 'user__email', 'user__username', 'tx_hash', 'crypto__symbol')
    readonly_fields = ('transaction_id', 'timestamp', 'updated_at', 'status')
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
    list_display = ('transaction', 'user', 'wallet_currency_display', 'destination_address', 'get_status', 'is_email_confirmed', 'confirmed_by_admin')
    list_filter = ('is_email_confirmed', 'confirmed_by_admin', 'wallet__currency__symbol', 'transaction__status')
    search_fields = ('user__email', 'user__username', 'transaction__transaction_id', 'destination_address', 'wallet__currency__symbol')
    readonly_fields = ('transaction', 'user', 'wallet', 'destination_address', 'is_email_confirmed', 'get_transaction_status', 'change_status')
    actions = ['approve_withdrawals', 'cancel_withdrawals', 'process_pending']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = None
    
    def get_form(self, request, obj=None, **kwargs):
        # Сохраняем request для использования в других методах
        self.request = request
        return super().get_form(request, obj, **kwargs)
    
    def get_fieldsets(self, request, obj=None):
        # Добавляем поле статуса в fieldsets
        if obj:
            return (
                (None, {
                    'fields': ('transaction', 'user', 'wallet', 'destination_address', 'get_transaction_status')
                }),
                ('Действия', {
                    'fields': ('change_status',),
                }),
                ('Confirmation', {
                    'fields': ('is_email_confirmed', 'confirmed_by_admin', 'rejected_reason', 'confirmation_date')
                }),
            )
        return super().get_fieldsets(request, obj)

    def wallet_currency_display(self, obj):
        if obj.wallet:
            return obj.wallet.currency.symbol
        return "-"
    wallet_currency_display.short_description = 'Валюта кошелька'

    def has_add_permission(self, request):
        return False

    def cancel_withdrawals(self, request, queryset):
        """Отменяет выбранные выводы средств"""
        for withdrawal in queryset:
            if withdrawal.transaction.status == 'pending':
                withdrawal.transaction.status = 'cancelled'
                withdrawal.transaction.save()
    cancel_withdrawals.short_description = "Отменить выбранные выводы средств"

    def approve_withdrawals(self, request, queryset):
        """Автоматически проверяет выбранные выводы на подтверждение в блокчейне"""
        from crypto.tasks import check_withdrawal_confirmation
        from .models import Transfer

        approved_count = 0
        for withdrawal in queryset.filter(transaction__status='awaiting_confirmation', is_email_confirmed=True):
            # Создаем или находим соответствующий Transfer
            transfer, created = Transfer.objects.get_or_create(
                withdrawal=withdrawal,
                defaults={
                    'user': withdrawal.user,
                    'amount': withdrawal.transaction.amount,
                    'status': Transfer.Status.PENDING,
                    'type': 'out'
                }
            )
            if created:
                self.message_user(request, f"Создан новый Transfer {transfer.id} для вывода {withdrawal.id}")

            # Запускаем проверку подтверждения в блокчейне
            check_withdrawal_confirmation.delay(withdrawal.id)
            approved_count += 1
        
        if approved_count > 0:
            self.message_user(request, f"Успешно запущено {approved_count} проверок подтверждения в блокчейне.")
        else:
            self.message_user(request, "Не найдено выводов для проверки (возможно, они уже завершены или не подтверждены по email).", level='WARNING')
    approve_withdrawals.short_description = "✅ Запустить проверку подтверждения в блокчейне"

    def process_pending(self, request, queryset):
        """Запускает обработку ожидающих выводов."""
        from crypto.tasks import process_pending_withdrawals
        process_pending_withdrawals.delay()
        self.message_user(request, "Запущена задача обработки ожидающих выводов.")
    process_pending.short_description = "⚙️ Обработать ожидающие выводы"

    def get_status(self, obj):
        return obj.transaction.get_status_display()
    get_status.short_description = 'Статус'
    
    def get_transaction_status(self, obj):
        """Отображает текущий статус транзакции"""
        from django.utils.html import format_html
        status = obj.transaction.status
        status_display = obj.transaction.get_status_display()
        
        # Цветовое оформление в зависимости от статуса
        if status == 'completed':
            color = 'green'
        elif status == 'pending':
            color = 'orange'
        elif status == 'processing':
            color = 'blue'
        elif status in ['cancelled', 'failed']:
            color = 'red'
        else:
            color = 'gray'
            
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, status_display)
    get_transaction_status.short_description = 'Текущий статус'
    
    def change_status(self, obj):
        """Отображает ссылки для изменения статуса"""
        from django.utils.html import format_html
        from transactions.models import Transaction
        
        # Словарь с русскими названиями статусов
        status_names = {
            'pending': 'В ожидании',
            'processing': 'В обработке',
            'completed': 'Завершено',
            'failed': 'Ошибка',
            'cancelled': 'Отменено',
            'refunded': 'Возвращено'
        }
        
        links = []
        for status_code, status_name in Transaction.STATUS_CHOICES:
            # Получаем русское название статуса
            ru_status_name = status_names.get(status_code, status_name)
            
            # Если это текущий статус, показываем его жирным шрифтом
            if status_code == obj.transaction.status:
                links.append(f'<b>{ru_status_name}</b>')
            else:
                # Иначе создаем ссылку для изменения статуса
                links.append(
                    f'<a href="/admin/transactions/withdrawal/{obj.id}/change-status/{status_code}/">{ru_status_name}</a>'
                )
        
        # Соединяем все ссылки через разделитель
        return format_html(' | '.join(links))
    
    change_status.short_description = 'Изменить статус'
    
    def get_urls(self):
        from django.urls import path
        from functools import update_wrapper
        
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)
        
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        
        custom_urls = [
            path('<path:object_id>/change-status/', wrap(self.change_status_view), name='%s_%s_change_status' % info),
            path('<path:object_id>/change-status/<str:new_status>/', wrap(self.change_status_direct_view), name='%s_%s_change_status_direct' % info),
        ]
        return custom_urls + urls
    
    def change_status_view(self, request, object_id, form_url=''):
        """Обработчик запроса на изменение статуса"""
        import json
        from django.http import JsonResponse
        import traceback
        
        if request.method != 'POST':
            return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
        
        try:
            # Получаем объект Withdrawal
            withdrawal = self.model.objects.get(pk=object_id)
            
            # Получаем новый статус из запроса
            data = json.loads(request.body)
            new_status = data.get('status')
            
            if not new_status:
                return JsonResponse({'error': 'Status not provided'}, status=400)
                
            # Устанавливаем новый статус
            withdrawal.transaction.status = new_status
            withdrawal.transaction.save()
            
            # Получаем отображаемое имя статуса
            from transactions.models import Transaction
            status_choices = dict(Transaction.STATUS_CHOICES)
            status_display = status_choices.get(new_status, new_status)
            
            return JsonResponse({
                'success': True, 
                'status': new_status,
                'status_display': status_display
            })
                
        except Exception as e:
            print(f"Error in change_status_view: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)

    def change_status_direct_view(self, request, object_id, new_status):
        """Обработчик запроса на прямое изменение статуса через GET-запрос"""
        from django.http import HttpResponseRedirect
        from django.contrib import messages
        import traceback
        
        try:
            # Получаем объект Withdrawal
            withdrawal = self.model.objects.get(pk=object_id)
            
            # Проверяем, что новый статус допустим
            from transactions.models import Transaction
            valid_statuses = [status[0] for status in Transaction.STATUS_CHOICES]
            
            if new_status not in valid_statuses:
                messages.error(request, f"Недопустимый статус: {new_status}")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            
            # Устанавливаем новый статус
            withdrawal.transaction.status = new_status
            withdrawal.transaction.save()
            
            # Словарь с русскими названиями статусов
            status_names = {
                'pending': 'В ожидании',
                'processing': 'В обработке',
                'completed': 'Завершено',
                'failed': 'Ошибка',
                'cancelled': 'Отменено',
                'refunded': 'Возвращено'
            }
            
            # Получаем русское название статуса
            ru_status_name = status_names.get(new_status, new_status)
            
            messages.success(request, f"Статус успешно изменен на '{ru_status_name}'")
                
        except Exception as e:
            print(f"Ошибка в change_status_direct_view: {str(e)}")
            print(traceback.format_exc())
            messages.error(request, f"Ошибка при изменении статуса: {str(e)}")
        
        # Возвращаемся на страницу редактирования
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


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

