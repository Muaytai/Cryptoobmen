"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
# Путь к файлу .env относительно текущего файла
env_path = Path(__file__).resolve().parent.parent / '.env'
# Пробуем загрузить .env из директории backend
if not os.path.exists(env_path):
    # Если файл не найден, пробуем загрузить из корня проекта
    env_path = Path(__file__).resolve().parent.parent.parent / '.env'

load_dotenv(env_path)

# Установка переменных окружения Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

from django.core.wsgi import get_wsgi_application

# Получаем WSGI-приложение
application = get_wsgi_application()
