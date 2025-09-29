from django.core.management.base import BaseCommand
from transactions.models import Withdrawal
from crypto.tasks import process_withdrawal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Тестировать обработку выводов как в админке'

    def add_arguments(self, parser):
        parser.add_argument('--withdrawal-id', type=int, help='ID конкретного вывода для обработки')
        parser.add_argument('--list', action='store_true', help='Показать список выводов')
        parser.add_argument('--approve', action='store_true', help='Подтвердить вывод перед обработкой')

    def handle(self, *args, **options):
        if options['list']:
            self.show_withdrawals()
            return
            
        withdrawal_id = options.get('withdrawal_id')
        if not withdrawal_id:
            self.stdout.write(self.style.ERROR("Укажите --withdrawal-id"))
            self.show_withdrawals()
            return
            
        try:
            withdrawal = Withdrawal.objects.get(id=withdrawal_id)
            
            self.stdout.write(f"📋 Обработка вывода ID {withdrawal.id}:")
            self.stdout.write(f"   Пользователь: {withdrawal.user.id}")
            self.stdout.write(f"   Сумма: {withdrawal.transaction.amount} {withdrawal.wallet.currency.symbol}")
            self.stdout.write(f"   Адрес: {withdrawal.destination_address}")
            self.stdout.write(f"   Email подтвержден: {withdrawal.is_email_confirmed}")
            self.stdout.write(f"   Админ подтвердил: {withdrawal.confirmed_by_admin}")
            self.stdout.write(f"   Статус: {withdrawal.transaction.status}")
            
            if options['approve'] and not withdrawal.confirmed_by_admin:
                self.stdout.write("✅ Подтверждаю вывод админом...")
                withdrawal.confirmed_by_admin = True
                withdrawal.transaction.status = 'pending'
                withdrawal.save()
                withdrawal.transaction.save()
                
            if withdrawal.transaction.status != 'pending':
                self.stdout.write(self.style.WARNING(f"Вывод не в статусе pending: {withdrawal.transaction.status}"))
                return
                
            if not withdrawal.is_email_confirmed:
                self.stdout.write(self.style.ERROR("Email не подтвержден"))
                return
                
            if not withdrawal.confirmed_by_admin:
                self.stdout.write(self.style.ERROR("Админ не подтвердил. Используйте --approve"))
                return
                
            self.stdout.write("🚀 Запуск обработки вывода синхронно...")
            result = process_withdrawal(withdrawal.id)
            self.stdout.write(self.style.SUCCESS(f"✅ Результат: {result}"))
            
        except Withdrawal.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Вывод с ID {withdrawal_id} не найден"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка: {e}"))
            import traceback
            traceback.print_exc()

    def show_withdrawals(self):
        self.stdout.write("📊 Доступные выводы:")
        withdrawals = Withdrawal.objects.all().order_by('-id')[:10]
        
        if not withdrawals:
            self.stdout.write("  Нет выводов")
            return
            
        for w in withdrawals:
            status_icon = "✅" if w.transaction.status == "completed" else "⏳" if w.transaction.status == "pending" else "❌"
            email_icon = "📧" if w.is_email_confirmed else "✉️"
            admin_icon = "👤" if w.confirmed_by_admin else "👥"
            
            self.stdout.write(
                f"  {status_icon} ID {w.id}: {w.transaction.amount} {w.wallet.currency.symbol} "
                f"({w.transaction.status}) {email_icon} {admin_icon}"
            )
