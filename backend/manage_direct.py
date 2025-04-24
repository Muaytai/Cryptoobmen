#!/usr/bin/env python
"""Django's command-line utility for administrative tasks with direct PostgreSQL connection."""
import os
import sys
import locale
from dotenv import load_dotenv

def main():
    """Run administrative tasks."""
    # Для Windows установим правильную локаль
    if sys.platform == 'win32':
        try:
            locale.setlocale(locale.LC_ALL, 'Russian_Russia.1251')
            print(f"Установлена локаль: {locale.getlocale()}")
        except Exception as e:
            print(f"Предупреждение: не удалось установить локаль: {e}")
    
    # Загружаем настройки из .env файла
    load_dotenv()
    
    # Получаем параметры подключения к БД
    db_engine = os.getenv('DB_ENGINE', 'django.db.backends.postgresql')
    db_name = os.getenv('DB_NAME', 'Crypto')
    db_user = os.getenv('DB_USER', 'postgres')
    db_host = os.getenv('DB_HOST', 'localhost')
    
    print(f"Подключение к базе данных {db_name} на {db_host} (движок: {db_engine})")
    
    # Патч для psycopg2, чтобы явно указать кодировку
    try:
        import psycopg2
        
        # Сохраняем оригинальную функцию подключения
        original_connect = psycopg2.connect
        
        # Создаем новую функцию подключения с параметрами кодировки
        def patched_connect(*args, **kwargs):
            # Добавляем параметры для правильной работы кодировки
            if 'options' not in kwargs:
                kwargs['options'] = "-c client_encoding=UTF8 -c standard_conforming_strings=on"
            return original_connect(*args, **kwargs)
        
        # Заменяем оригинальную функцию нашей
        psycopg2.connect = patched_connect
        print("✓ Патч psycopg2 успешно установлен для корректной работы с кириллицей")
    except ImportError:
        print("⚠ psycopg2 не установлен, патч не применен")
    
    # Настройка Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
        print("✓ Django успешно импортирован")
        
        # Импортируем и используем нашу утилиту настройки соединения
        try:
            from core.utils import setup_postgresql_connection
            setup_postgresql_connection()
            print("✓ Настройки PostgreSQL-соединения применены")
        except ImportError:
            print("⚠ Не удалось импортировать утилиту настройки соединения")
        
        # Запускаем команду Django
        print("Запуск Django команды:", " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "")
        execute_from_command_line(sys.argv)
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc


if __name__ == '__main__':
    main() 