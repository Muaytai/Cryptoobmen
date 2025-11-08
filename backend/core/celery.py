from __future__ import absolute_import, unicode_literals
import os
from celery import Celery


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
