from django.apps import AppConfig
import os
import sys


class CryptoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crypto'
    
    def ready(self):
        # Импортируем сигналы для их регистрации
        from . import signals
        
        # Создаем валюты по умолчанию (только в основном процессе)
        if os.environ.get('RUN_MAIN') != 'true':
            return
            
        from .models import create_default_cryptocurrencies
        try:
            create_default_cryptocurrencies()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f'Не удалось автосоздать валюты: {e}')

        # --- Автоматическая регистрация задачи Celery Beat при первом запуске ---
        # Это необходимо, когда используется DatabaseScheduler из django_celery_beat,
        # иначе статический CELERY_BEAT_SCHEDULE в settings.py игнорируется.
        # Создаём запись PeriodicTask каждые 30 секунд, если она ещё не существует.

        # Запускаем логику только в веб-процессе / manage.py runserver / gunicorn.
        if any(cmd in sys.argv[0] for cmd in ("gunicorn", "uvicorn", "runserver")) or (
            len(sys.argv) > 1 and sys.argv[1] in ("runserver", "uwsgi")):
            try:
                from django_celery_beat.models import PeriodicTask, IntervalSchedule
                from celery import current_app

                task_name = "crypto.tasks.check_blockchain_deposits"
                # Проверяем, зарегистрирована ли задача в Celery
                if task_name not in current_app.tasks:
                    return  # задача ещё не импортирована, пропускаем

                schedule, _ = IntervalSchedule.objects.get_or_create(every=30, period=IntervalSchedule.SECONDS)

                PeriodicTask.objects.get_or_create(
                    name="Scan TRC20 deposits (every 30s)",
                    task=task_name,
                    defaults={"interval": schedule, "enabled": True},
                )
            except Exception:  # noqa: BLE001 – игнорируем любые ошибки БД при миграциях
                pass
