"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import sys
import locale
from pathlib import Path
from dotenv import load_dotenv

# Для Windows установить правильную локаль для работы с кириллицей
if sys.platform == 'win32':
    try:
        locale.setlocale(locale.LC_ALL, 'Russian_Russia.1251')
    except Exception as e:
        print(f"Предупреждение: не удалось установить локаль: {e}")

# Загрузка переменных окружения из .env файла
# Путь к файлу .env относительно текущего файла
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(env_path)

# Установка переменных окружения Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

from django.core.wsgi import get_wsgi_application
from core.utils import setup_postgresql_connection

# Получаем WSGI-приложение
application = get_wsgi_application()

# Настраиваем корректное подключение к PostgreSQL
setup_postgresql_connection()
