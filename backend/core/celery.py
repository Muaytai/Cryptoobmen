from __future__ import absolute_import, unicode_literals
import os
from celery import Celery


# Имя настроечного модуля Django берём из переменной окружения
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

app = Celery("core")

# Читаем конфиги Celery из переменных окружения с префиксом CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматически находит и регистрирует все задачи из installed apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Простейшая задача для проверки работоспособности Celery."""
    print(f"Request: {self.request!r}")
