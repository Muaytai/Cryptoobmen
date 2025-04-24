import os
import sys
import locale
from django.db import connections

def setup_postgresql_connection():
    """
    Настраивает корректное подключение к PostgreSQL на Windows.
    Рекомендуется вызывать в файле wsgi.py перед запуском приложения.
    """
    # Проверяем, используется ли PostgreSQL и Windows
    if sys.platform == 'win32' and os.environ.get('DB_ENGINE') == 'django.db.backends.postgresql':
        try:
            # Устанавливаем русскую локаль для Windows
            locale.setlocale(locale.LC_ALL, 'Russian_Russia.1251')
            
            # Если нужно применить настройки к текущим соединениям
            for conn in connections.all():
                if conn.vendor == 'postgresql':
                    # Устанавливаем кодировку для текущих соединений
                    conn.cursor().execute("SET client_encoding TO 'UTF8';")
                    
            return True
        except Exception as e:
            print(f"Ошибка настройки PostgreSQL: {e}")
            return False
    
    return True 