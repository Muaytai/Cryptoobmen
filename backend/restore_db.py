#!/usr/bin/env python3
"""
Скрипт для восстановления базы данных из JSON бэкапа.
Использует Django команду loaddata.
Настройка файла бэкапа: измените переменную BACKUP_FILE в начале скрипта.
"""
import os
import sys
import gzip
import tempfile
from pathlib import Path
import django
from django.core.management import call_command
from django.conf import settings

# ============================================
# НАСТРОЙКА ФАЙЛА БЭКАПА
# ============================================
# Укажите путь к файлу бэкапа для восстановления
# Можно указать абсолютный путь или относительный от директории проекта
# Поддерживаются форматы: .json и .json.gz
BACKUP_FILE = 'backups/cryptoobmen_backup_20251117_152501.json.gz'  # Измените на нужный файл
# ============================================

# Настройка Django окружения
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()


def restore_backup(backup_file_path):
    """Восстанавливает базу данных из JSON бэкапа"""
    db_config = settings.DATABASES['default']
    db_name = db_config['NAME']
    
    # Определяем путь к файлу бэкапа
    if os.path.isabs(backup_file_path):
        backup_path = Path(backup_file_path)
    else:
        backup_path = BASE_DIR / backup_file_path
    
    # Проверяем существование файла
    if not backup_path.exists():
        print(f"❌ Файл бэкапа не найден: {backup_path}")
        sys.exit(1)
    
    # Определяем, сжат ли файл
    is_compressed = backup_path.suffix == '.gz' or backup_path.suffixes[-1] == '.gz'
    
    try:
        print(f"Восстановление базы данных {db_name} из бэкапа...")
        print(f"Файл: {backup_path}")
        
        # Подтверждение перед восстановлением
        print("\n⚠️  ВНИМАНИЕ: Все данные в базе данных будут заменены!")
        response = input("Продолжить? (yes/no): ")
        if response.lower() not in ['yes', 'y', 'да', 'д']:
            print("Восстановление отменено.")
            sys.exit(0)
        
        # Если файл сжат, распаковываем во временный файл вне папки backups
        if is_compressed:
            print("Распаковка сжатого файла...")
            # Создаем временный файл с уникальным именем
            temp_fd, temp_json_path = tempfile.mkstemp(suffix='.json', prefix='restore_', dir=None)
            os.close(temp_fd)  # Закрываем файловый дескриптор, нам нужен только путь
            
            with gzip.open(backup_path, 'rb') as f_in:
                with open(temp_json_path, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            json_file_path = Path(temp_json_path)
        else:
            json_file_path = backup_path
        
        print("\nВыполнение восстановления...")
        
        # Выполняем loaddata с абсолютным путем
        call_command('loaddata', str(json_file_path.resolve()), verbosity=1)
        
        # Удаляем временный файл, если был создан
        if is_compressed and json_file_path.exists():
            json_file_path.unlink()
        
        print("✅ База данных успешно восстановлена!")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при восстановлении базы данных: {e}")
        # Удаляем временный файл при ошибке
        if is_compressed and 'json_file_path' in locals():
            if json_file_path.exists():
                json_file_path.unlink()
        sys.exit(1)


if __name__ == '__main__':
    restore_backup(BACKUP_FILE)
