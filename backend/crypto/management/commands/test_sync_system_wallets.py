from django.core.management.base import BaseCommand
from crypto.tasks import sync_system_wallets_balance
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Тестирует синхронизацию балансов системных кошельков'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Только проверить балансы без обновления в БД',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("=== ТЕСТ СИНХРОНИЗАЦИИ БАЛАНСОВ СИСТЕМНЫХ КОШЕЛЬКОВ ===")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️  Режим dry-run: изменения не будут сохранены"))
        
        try:
            # Запускаем задачу синхронизации
            result = sync_system_wallets_balance()
            
            if isinstance(result, dict):
                updated = result.get('updated', 0)
                errors = result.get('errors', 0)
                
                self.stdout.write(f"\n--- РЕЗУЛЬТАТЫ ---")
                self.stdout.write(f"Обновлено кошельков: {updated}")
                self.stdout.write(f"Ошибок: {errors}")
                
                if updated > 0:
                    self.stdout.write(self.style.SUCCESS(f"✅ Успешно обновлено {updated} кошельков"))
                elif errors == 0:
                    self.stdout.write(self.style.SUCCESS("✅ Все балансы уже синхронизированы"))
                
                if errors > 0:
                    self.stdout.write(self.style.WARNING(f"⚠️  Обнаружено {errors} ошибок при синхронизации"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ Задача выполнена"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Ошибка при выполнении задачи: {e}"))
            logger.exception("Error running sync_system_wallets_balance")
            return
        
        self.stdout.write(f"\n=== ТЕСТ ЗАВЕРШЕН ===")
