from django.core.management.base import BaseCommand
from crypto.tasks import check_blockchain_deposits
from crypto.tasks_consolidation import consolidate_user_deposits
from transactions.models import Transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Тестировать автоматическую консолидацию после депозитов'

    def add_arguments(self, parser):
        parser.add_argument('--force-consolidation', action='store_true', 
                          help='Принудительно запустить консолидацию без сканирования')

    def handle(self, *args, **options):
        if options['force_consolidation']:
            self.stdout.write("🔧 Принудительная консолидация...")
            result = consolidate_user_deposits()
            self.stdout.write(f"✅ {result}")
            return

        self.stdout.write("🔍 Тестирование автоматической консолидации...")
        
        # Проверим последние транзакции до
        before_count = Transaction.objects.filter(type='consolidation').count()
        self.stdout.write(f"Транзакций консолидации до: {before_count}")
        
        # Имитируем обнаружение нового депозита (запускаем задачу)
        self.stdout.write("📡 Запуск задачи сканирования депозитов...")
        
        try:
            # Используем прямой вызов функции вместо celery task
            from crypto.tasks_consolidation import consolidate_user_deposits
            self.stdout.write("🚀 Запуск консолидации напрямую...")
            
            result = consolidate_user_deposits()
            self.stdout.write(f"✅ Результат консолидации: {result}")
            
            # Проверим количество после
            after_count = Transaction.objects.filter(type='consolidation').count()
            self.stdout.write(f"Транзакций консолидации после: {after_count}")
            
            if after_count > before_count:
                self.stdout.write(self.style.SUCCESS(f"✅ Создано {after_count - before_count} новых консолидаций"))
            else:
                self.stdout.write(self.style.WARNING("⚠️ Новых консолидаций не создано"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка: {e}"))
            
        # Показать последние транзакции
        self.stdout.write("\n📊 Последние транзакции:")
        recent_txs = Transaction.objects.filter(
            crypto__symbol='POL'
        ).order_by('-timestamp')[:5]
        
        for tx in recent_txs:
            status_icon = "✅" if tx.status == "completed" else "⏳" if tx.status == "pending" else "❌"
            self.stdout.write(f"  {status_icon} {tx.type}: {tx.amount} POL ({tx.status}) - {tx.timestamp.strftime('%H:%M:%S')}")
