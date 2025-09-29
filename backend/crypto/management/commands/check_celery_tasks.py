from django.core.management.base import BaseCommand
from celery import current_app
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Проверяет регистрацию задач Celery, включая задачи консолидации'

    def handle(self, *args, **options):
        self.stdout.write("=== Проверка регистрации задач Celery ===\n")
        
        try:
            # Получаем все зарегистрированные задачи
            tasks = current_app.tasks
            self.stdout.write(f"Всего зарегистрированных задач: {len(tasks)}")
            
            # Ищем задачи консолидации
            consolidation_tasks = []
            crypto_tasks = []
            
            for task_name in sorted(tasks.keys()):
                if 'consolidation' in task_name.lower():
                    consolidation_tasks.append(task_name)
                elif task_name.startswith('crypto.'):
                    crypto_tasks.append(task_name)
            
            # Отображаем задачи консолидации
            self.stdout.write(f"\n--- ЗАДАЧИ КОНСОЛИДАЦИИ ---")
            if consolidation_tasks:
                for task in consolidation_tasks:
                    self.stdout.write(f"✓ {task}")
            else:
                self.stdout.write("⚠ Задачи консолидации не найдены!")
            
            # Отображаем остальные crypto задачи
            self.stdout.write(f"\n--- ДРУГИЕ CRYPTO ЗАДАЧИ ---")
            if crypto_tasks:
                for task in crypto_tasks:
                    self.stdout.write(f"✓ {task}")
            else:
                self.stdout.write("⚠ Crypto задачи не найдены!")
            
            # Проверяем конкретные задачи из настроек
            expected_tasks = [
                'crypto.tasks.check_blockchain_deposits',
                'crypto.tasks.process_pending_withdrawals',
                'crypto.tasks.process_pending_deposits',
                'crypto.tasks_consolidation.consolidate_user_deposits',
                'crypto.tasks_consolidation.check_consolidation_confirmations',
                'crypto.tasks.consolidate_funds',
            ]
            
            self.stdout.write(f"\n--- ПРОВЕРКА ЗАДАЧ ИЗ НАСТРОЕК ---")
            missing_tasks = []
            
            for task_name in expected_tasks:
                if task_name in tasks:
                    self.stdout.write(f"✓ {task_name}")
                else:
                    self.stdout.write(f"✗ {task_name} - НЕ НАЙДЕНА!")
                    missing_tasks.append(task_name)
            
            # Проверяем CELERY_BEAT_SCHEDULE
            self.stdout.write(f"\n--- ПРОВЕРКА CELERY_BEAT_SCHEDULE ---")
            from django.conf import settings
            
            if hasattr(settings, 'CELERY_BEAT_SCHEDULE'):
                beat_schedule = settings.CELERY_BEAT_SCHEDULE
                self.stdout.write(f"Запланированных задач: {len(beat_schedule)}")
                
                for schedule_name, config in beat_schedule.items():
                    task_name = config.get('task')
                    schedule = config.get('schedule')
                    
                    if task_name in tasks:
                        self.stdout.write(f"✓ {schedule_name}: {task_name} (каждые {schedule}с)")
                    else:
                        self.stdout.write(f"✗ {schedule_name}: {task_name} - ЗАДАЧА НЕ НАЙДЕНА!")
            else:
                self.stdout.write("✗ CELERY_BEAT_SCHEDULE не найден в настройках!")
            
            # Проверяем импорт задач консолидации
            self.stdout.write(f"\n--- ПРОВЕРКА ИМПОРТА ---")
            try:
                from crypto.tasks_consolidation import consolidate_user_deposits, check_consolidation_confirmations
                self.stdout.write("✓ crypto.tasks_consolidation импортирован успешно")
                self.stdout.write(f"✓ consolidate_user_deposits: {consolidate_user_deposits}")
                self.stdout.write(f"✓ check_consolidation_confirmations: {check_consolidation_confirmations}")
            except ImportError as e:
                self.stdout.write(f"✗ Ошибка импорта crypto.tasks_consolidation: {e}")
            
            # Итоги
            self.stdout.write(f"\n--- ИТОГИ ---")
            if missing_tasks:
                self.stdout.write(self.style.ERROR(f"✗ Отсутствует {len(missing_tasks)} задач:"))
                for task in missing_tasks:
                    self.stdout.write(f"  - {task}")
                self.stdout.write("\n🔧 Для исправления:")
                self.stdout.write("1. Проверьте импорты в crypto/tasks_consolidation.py")
                self.stdout.write("2. Убедитесь что задачи помечены @shared_task")
                self.stdout.write("3. Перезапустите Celery worker и beat")
            else:
                self.stdout.write(self.style.SUCCESS("✅ Все ожидаемые задачи зарегистрированы!"))
                self.stdout.write("\n🚀 Для запуска:")
                self.stdout.write("celery -A core beat -l info")
                self.stdout.write("celery -A core worker -l info")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Критическая ошибка: {e}"))
            logger.exception("Критическая ошибка в check_celery_tasks")

        self.stdout.write(f"\n=== Проверка завершена ===")