from __future__ import absolute_import, unicode_literals
import os
import logging
from celery import Celery
from celery.utils.log import get_task_logger


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

# Автоматически находит и регистрирует все задачи из installed apps
app.autodiscover_tasks()

# Убеждаемся, что все модули с задачами зарегистрированы
app.autodiscover_tasks(['crypto'], related_name='tasks_consolidation')


@app.task(bind=True)
def debug_task(self):
    """Простейшая задача для проверки работоспособности Celery."""
    print(f"Request: {self.request!r}")
