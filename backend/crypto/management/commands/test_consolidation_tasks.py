from django.core.management.base import BaseCommand
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Тестирует запуск задач консолидации вручную'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-consolidation',
            action='store_true',
            help='Запустить задачу консолидации напрямую',
        )
        parser.add_argument(
            '--test-check-confirmations',
            action='store_true',
            help='Запустить проверку подтверждений напрямую',
        )
        parser.add_argument(
            '--check-schedule',
            action='store_true',
            help='Проверить настройки расписания',
        )

    def handle(self, *args, **options):
        self.stdout.write("=== Тестирование задач консолидации ===\n")
        
        try:
            # Проверяем настройки
            if options.get('check_schedule'):
                self.stdout.write("--- ПРОВЕРКА CELERY_BEAT_SCHEDULE ---")
                
                if hasattr(settings, 'CELERY_BEAT_SCHEDULE'):
                    schedule = settings.CELERY_BEAT_SCHEDULE
                    self.stdout.write(f"Найдено задач в расписании: {len(schedule)}")
                    
                    for name, config in schedule.items():
                        task_name = config.get('task', 'N/A')
                        schedule_time = config.get('schedule', 'N/A')
                        queue = config.get('options', {}).get('queue', 'default')
                        
                        self.stdout.write(f"  {name}:")
                        self.stdout.write(f"    Задача: {task_name}")
                        self.stdout.write(f"    Расписание: {schedule_time}s")
                        self.stdout.write(f"    Очередь: {queue}")
                        
                        # Проверяем, есть ли задача в Celery
                        try:
                            from celery import current_app
                            if task_name in current_app.tasks:
                                self.stdout.write(f"    ✓ Задача зарегистрирована в Celery")
                            else:
                                self.stdout.write(f"    ✗ Задача НЕ зарегистрирована в Celery")
                        except Exception as e:
                            self.stdout.write(f"    ⚠ Ошибка проверки: {e}")
                        
                        self.stdout.write("")
                else:
                    self.stdout.write("✗ CELERY_BEAT_SCHEDULE не найден!")
                
                return
            
            # Тестируем прямой импорт и вызов задач
            self.stdout.write("--- ТЕСТИРОВАНИЕ ИМПОРТА ЗАДАЧ ---")
            
            try:
                from crypto.tasks_consolidation import consolidate_user_deposits, check_consolidation_confirmations
                self.stdout.write("✓ Задачи консолидации импортированы успешно")
                
                # Проверяем, что это Celery задачи
                if hasattr(consolidate_user_deposits, 'delay'):
                    self.stdout.write("✓ consolidate_user_deposits - Celery задача")
                else:
                    self.stdout.write("✗ consolidate_user_deposits - НЕ Celery задача")
                    
                if hasattr(check_consolidation_confirmations, 'delay'):
                    self.stdout.write("✓ check_consolidation_confirmations - Celery задача")
                else:
                    self.stdout.write("✗ check_consolidation_confirmations - НЕ Celery задача")
                
            except ImportError as e:
                self.stdout.write(f"✗ Ошибка импорта: {e}")
                return
            
            # Тестируем выполнение задач
            if options.get('test_consolidation'):
                self.stdout.write("\n--- ТЕСТИРОВАНИЕ КОНСОЛИДАЦИИ ---")
                try:
                    result = consolidate_user_deposits()
                    self.stdout.write(f"✅ Результат: {result}")
                except Exception as e:
                    self.stdout.write(f"✗ Ошибка: {e}")
                    logger.exception("Ошибка при тестировании консолидации")
            
            if options.get('test_check_confirmations'):
                self.stdout.write("\n--- ТЕСТИРОВАНИЕ ПРОВЕРКИ ПОДТВЕРЖДЕНИЙ ---")
                try:
                    result = check_consolidation_confirmations()
                    self.stdout.write(f"✅ Результат: {result}")
                except Exception as e:
                    self.stdout.write(f"✗ Ошибка: {e}")
                    logger.exception("Ошибка при тестировании проверки подтверждений")
            
            if not any([options.get('test_consolidation'), options.get('test_check_confirmations')]):
                self.stdout.write("\n💡 Доступные опции:")
                self.stdout.write("  --test-consolidation        - запустить консолидацию")
                self.stdout.write("  --test-check-confirmations  - проверить подтверждения")
                self.stdout.write("  --check-schedule            - проверить расписание")
                
                self.stdout.write("\n🚀 Для запуска Celery Beat:")
                self.stdout.write("  celery -A core beat -l info")
                self.stdout.write("\n🚀 Для запуска Celery Worker:")
                self.stdout.write("  celery -A core worker -l info")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Критическая ошибка: {e}"))
            logger.exception("Критическая ошибка в test_consolidation_tasks")

        self.stdout.write(f"\n=== Тестирование завершено ===")