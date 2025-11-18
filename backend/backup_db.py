#!/usr/bin/env python3
"""
Скрипт для создания бэкапа базы данных в формате JSON.
Использует Django команду dumpdata.
"""
import os
import sys
import gzip
from pathlib import Path
from datetime import datetime
import django
from django.conf import settings
from django.core.management import call_command

# Настройка Django окружения
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()


def create_backup():
    """Создает бэкап базы данных в формате JSON"""
    db_config = settings.DATABASES['default']
    db_name = db_config['NAME']
    
    # Создаем директорию для бэкапов, если её нет
    backup_dir = BASE_DIR / 'backups'
    backup_dir.mkdir(exist_ok=True)
    
    # Генерируем имя файла бэкапа с датой и временем
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'{db_name}_backup_{timestamp}.json.gz'
    backup_path = backup_dir / backup_filename
    
    try:
        print(f"Создание бэкапа базы данных {db_name}...")
        print(f"Файл: {backup_path}")
        
        # Создаем временный файл для JSON
        temp_json_path = backup_path.with_suffix('.json')
        
        # Выполняем dumpdata в JSON файл
        with open(temp_json_path, 'w', encoding='utf-8') as f:
            call_command('dumpdata', 
                        exclude=['contenttypes', 'auth.Permission', 'sessions'],
                        natural_foreign=True,
                        natural_primary=True,
                        stdout=f,
                        verbosity=0)
        
        # Сжимаем JSON файл в gzip
        with open(temp_json_path, 'rb') as f_in:
            with gzip.open(backup_path, 'wb') as f_out:
                f_out.writelines(f_in)
        
        # Удаляем временный JSON файл
        temp_json_path.unlink()
        
        # Получаем размер файла
        file_size = backup_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        print("✅ Бэкап успешно создан!")
        print(f"   Размер: {file_size_mb:.2f} MB (сжатый)")
        print(f"   Путь: {backup_path}")
        
        return str(backup_path)
        
    except Exception as e:
        print(f"❌ Ошибка при создании бэкапа: {e}")
        # Удаляем временный файл при ошибке
        temp_json_path = backup_path.with_suffix('.json')
        if temp_json_path.exists():
            temp_json_path.unlink()
        sys.exit(1)


if __name__ == '__main__':
    create_backup()
