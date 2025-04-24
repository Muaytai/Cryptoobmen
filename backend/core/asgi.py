"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import sys
import locale
from dotenv import load_dotenv

# Для Windows установим правильную локаль
if sys.platform == 'win32':
    try:
        locale.setlocale(locale.LC_ALL, 'Russian_Russia.1251')
        print(f"ASGI: Локаль установлена: {locale.getlocale()}")
    except Exception as e:
        print(f"ASGI Предупреждение: не удалось установить локаль: {e}")

# Загружаем настройки из .env файла
load_dotenv()

# Установка переменных окружения Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

from django.core.asgi import get_asgi_application

application = get_asgi_application()
