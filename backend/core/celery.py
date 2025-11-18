from __future__ import absolute_import, unicode_literals
import os
import logging
from pathlib import Path
from celery import Celery
from celery.signals import worker_process_init
from celery.utils.log import get_task_logger



# Имя настроечного модуля Django берём из переменной окружения
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")


app = Celery("core")

# Читаем конфиги Celery из переменных окружения с префиксом CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматически находит и регистрирует все задачи из installed apps
app.autodiscover_tasks()

# Убеждаемся, что все модули с задачами зарегистрированы
app.autodiscover_tasks(['crypto'], related_name='tasks_consolidation')


@app.task(bind=True)
def debug_task(self):
    """Простейшая задача для проверки работоспособности Celery."""
    print(f"Request: {self.request!r}")




# Имя настроечного модуля Django берём из переменной окружения
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")


app = Celery("core")

# Читаем конфиги Celery из переменных окружения с префиксом CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Настройка цветного логирования для Celery
def setup_colored_logging():
    """Настройка цветного логирования для Celery"""
    # Получаем логгер для задач консолидации
    consolidation_logger = get_task_logger('crypto.tasks_consolidation')
    
    # Устанавливаем уровень логирования
    consolidation_logger.setLevel(logging.INFO)
    
    # Добавляем цветной обработчик если его еще нет
    if not any(isinstance(h, logging.StreamHandler) for h in consolidation_logger.handlers):
        from core.colored_formatter import ColoredFormatter
        handler = logging.StreamHandler()
        handler.setFormatter(ColoredFormatter(
            '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
        ))
        consolidation_logger.addHandler(handler)
        consolidation_logger.propagate = False

# Настраиваем цветное логирование
setup_colored_logging()


@worker_process_init.connect
def setup_log_rotation(sender=None, **kwargs):
    """Настройка ротации логов для Celery workers"""
    from django.conf import settings
    from logging.handlers import RotatingFileHandler
    
    BASE_DIR = Path(settings.BASE_DIR)
    log_dir = BASE_DIR / 'logs' / 'celery'
    
    # Список файлов логов Celery
    celery_log_files = [
        log_dir / 'beat.log',
        log_dir / 'high_priority.log',
        log_dir / 'medium_priority.log',
        log_dir / 'low_priority.log',
    ]
    
    # Проходим по всем логгерам и заменяем FileHandler на RotatingFileHandler
    root_logger = logging.getLogger()
    
    for handler in list(root_logger.handlers):
        if isinstance(handler, logging.FileHandler):
            handler_path = Path(handler.baseFilename)
            # Если это файл из директории celery логов
            if handler_path.parent == log_dir and handler_path.name.endswith('.log'):
                # Сохраняем форматтер
                formatter = handler.formatter
                # Закрываем старый handler
                handler.close()
                root_logger.removeHandler(handler)
                
                # Создаем новый RotatingFileHandler
                rotating_handler = RotatingFileHandler(
                    str(handler_path),
                    maxBytes=1024 * 1024,  # 1 MB
                    backupCount=5,
                    mode='a'
                )
                if formatter:
                    rotating_handler.setFormatter(formatter)
                root_logger.addHandler(rotating_handler)
    
    # Также обрабатываем логгеры celery.*
    for logger_name in ['celery', 'celery.beat', 'celery.worker']:
        logger = logging.getLogger(logger_name)
        for handler in list(logger.handlers):
            if isinstance(handler, logging.FileHandler):
                handler_path = Path(handler.baseFilename)
                if handler_path.parent == log_dir and handler_path.name.endswith('.log'):
                    formatter = handler.formatter
                    handler.close()
                    logger.removeHandler(handler)
                    
                    rotating_handler = RotatingFileHandler(
                        str(handler_path),
                        maxBytes=1024 * 1024,  # 1 MB
                        backupCount=5,
                        mode='a'
                    )
                    if formatter:
                        rotating_handler.setFormatter(formatter)
                    logger.addHandler(rotating_handler)

# Автоматически находит и регистрирует все задачи из installed apps
app.autodiscover_tasks()

# Убеждаемся, что все модули с задачами зарегистрированы
app.autodiscover_tasks(['crypto'], related_name='tasks_consolidation')


@app.task(bind=True)
def debug_task(self):
    """Простейшая задача для проверки работоспособности Celery."""
    print(f"Request: {self.request!r}")

