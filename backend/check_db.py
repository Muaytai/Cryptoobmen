#!/usr/bin/env python
"""
Скрипт проверки соединения с PostgreSQL
"""
import os
import sys
import locale
import platform
from dotenv import load_dotenv
from datetime import datetime

# Загружаем переменные окружения
load_dotenv()

# Параметры подключения
DB_ENGINE = os.getenv('DB_ENGINE', 'django.db.backends.postgresql')
DB_NAME = os.getenv('DB_NAME', 'Crypto')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

def check_connection():
    """Тестирование подключения к PostgreSQL"""
    print("\n=== Проверка соединения с PostgreSQL ===")
    
    # Прячем пароль в выводе
    connection_string = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER}"
    print(f"Подключение к: {connection_string}")
    
    try:
        import psycopg2
        
        # Устанавливаем русскую локаль для Windows
        if sys.platform == 'win32':
            try:
                locale.setlocale(locale.LC_ALL, 'Russian_Russia.1251')
                print(f"✓ Установлена локаль: {locale.getlocale()}")
            except Exception as e:
                print(f"⚠ Не удалось установить локаль: {e}")
        
        # Явно указываем параметры для кодировки
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            options="-c client_encoding=UTF8 -c standard_conforming_strings=on"
        )
        
        print(f"✓ Соединение с БД установлено успешно!")
        
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        print(f"✓ PostgreSQL версия: {version[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при подключении: {e}")
        return False

if __name__ == "__main__":
    print("=== Проверка подключения к базе данных ===")
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    check_connection() 