#!/usr/bin/env python3
"""
Скрипт для восстановления базы данных из JSON бэкапа
Использует Django ORM для импорта данных
"""

import os
import sys
import json
import logging
import argparse
import gzip
from datetime import datetime
from pathlib import Path

# Добавляем путь к Django проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка Django окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.conf import settings
from django.core import serializers
from django.db import transaction
from django.apps import apps


def setup_logging(log_level='INFO'):
    """Настройка логирования"""
    log_dir = Path(settings.BASE_DIR) / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f'restore_json_{datetime.now().strftime("%Y%m%d")}.log'
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def check_backup_file(backup_path):
    """Проверка существования и валидности JSON файла бэкапа"""
    logger = logging.getLogger(__name__)
    
    if not backup_path.exists():
        logger.error(f"Файл бэкапа не найден: {backup_path}")
        return False
    
    if not backup_path.is_file():
        logger.error(f"Указанный путь не является файлом: {backup_path}")
        return False
    
    # Проверяем размер файла
    file_size = backup_path.stat().st_size
    if file_size == 0:
        logger.error(f"Файл бэкапа пустой: {backup_path}")
        return False
    
    logger.info(f"Файл JSON бэкапа найден: {backup_path}")
    logger.info(f"Размер файла: {file_size / (1024*1024):.2f} MB")
    
    return True


def load_json_backup(backup_path):
    """Загрузка JSON бэкапа"""
    logger = logging.getLogger(__name__)
    
    try:
        # Определяем, сжат ли файл
        is_compressed = backup_path.suffix == '.gz'
        
        if is_compressed:
            with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
                backup_data = json.load(f)
        else:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
        
        logger.info(f"JSON бэкап успешно загружен (сжат: {is_compressed})")
        
        # Проверяем структуру бэкапа
        if 'metadata' not in backup_data or 'models' not in backup_data:
            logger.error("Неверный формат JSON бэкапа")
            return None
        
        metadata = backup_data['metadata']
        logger.info(f"Метаданные бэкапа:")
        logger.info(f"  Создан: {metadata.get('created_at', 'Неизвестно')}")
        logger.info(f"  Django версия: {metadata.get('django_version', 'Неизвестно')}")
        logger.info(f"  База данных: {metadata.get('database_name', 'Неизвестно')}")
        logger.info(f"  Моделей: {metadata.get('total_models', 0)}")
        logger.info(f"  Объектов: {metadata.get('total_objects', 0)}")
        
        return backup_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Ошибка при загрузке JSON бэкапа: {e}")
        return None


def clear_database():
    """Очистка базы данных"""
    logger = logging.getLogger(__name__)
    
    logger.warning("Очистка базы данных...")
    
    try:
        # Получаем все модели
        models = []
        for app_config in apps.get_app_configs():
            models.extend(app_config.get_models())
        
        # Удаляем данные в обратном порядке (с учетом зависимостей)
        models.reverse()
        
        total_deleted = 0
        for model in models:
            try:
                count = model.objects.count()
                if count > 0:
                    model.objects.all().delete()
                    logger.info(f"Удалено {count} объектов из модели {model.__name__}")
                    total_deleted += count
            except Exception as e:
                logger.warning(f"Не удалось очистить модель {model.__name__}: {e}")
        
        logger.info(f"Всего удалено объектов: {total_deleted}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при очистке базы данных: {e}")
        return False


def restore_model_data(model_data, logger):
    """Восстановление данных модели"""
    try:
        model_name = model_data['model']
        count = model_data['count']
        serialized_data = model_data['data']
        
        logger.info(f"Восстановление модели {model_name}: {count} объектов")
        
        if count == 0:
            logger.info(f"Модель {model_name}: нет данных для восстановления")
            return 0
        
        # Восстанавливаем данные через Django deserializer
        restored_count = 0
        for obj_data in serialized_data:
            try:
                obj = serializers.deserialize('python', [obj_data])
                for deserialized_obj in obj:
                    deserialized_obj.save()
                restored_count += 1
            except Exception as e:
                logger.warning(f"Ошибка при восстановлении объекта {obj_data.get('pk', 'unknown')}: {e}")
        
        logger.info(f"Восстановлено {restored_count} из {count} объектов модели {model_name}")
        return restored_count
        
    except Exception as e:
        logger.error(f"Ошибка при восстановлении модели {model_data.get('model', 'unknown')}: {e}")
        return 0


def restore_json_backup(backup_data, clear_db=True):
    """Восстановление базы данных из JSON бэкапа"""
    logger = logging.getLogger(__name__)
    
    try:
        models_data = backup_data['models']
        total_models = len(models_data)
        total_objects = backup_data['metadata'].get('total_objects', 0)
        
        logger.info(f"Начинаем восстановление из JSON бэкапа")
        logger.info(f"Моделей для восстановления: {total_models}")
        logger.info(f"Объектов для восстановления: {total_objects}")
        
        # Очищаем базу данных если требуется
        if clear_db:
            if not clear_database():
                logger.error("Не удалось очистить базу данных")
                return False
        
        # Восстанавливаем данные в транзакции
        with transaction.atomic():
            restored_objects = 0
            
            for model_data in models_data:
                count = restore_model_data(model_data, logger)
                restored_objects += count
            
            logger.info(f"Восстановлено объектов: {restored_objects}")
        
        logger.info("JSON бэкап успешно восстановлен!")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при восстановлении JSON бэкапа: {e}")
        return False


def create_json_backup_before_restore(backup_dir):
    """Создание JSON бэкапа текущей БД перед восстановлением"""
    logger = logging.getLogger(__name__)
    
    logger.warning("Создание JSON резервной копии текущей базы данных...")
    
    try:
        # Импортируем функцию создания бэкапа
        from backup_json import create_json_backup
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = create_json_backup(
            backup_dir, 
            compress=True,
            custom_name=f"pre_restore_backup_{timestamp}"
        )
        
        if backup_path:
            logger.info(f"JSON резервная копия создана: {backup_path}")
            return backup_path
        else:
            logger.error("Не удалось создать JSON резервную копию")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка при создании JSON резервной копии: {e}")
        return None


def run_migrations():
    """Запуск миграций Django"""
    logger = logging.getLogger(__name__)
    
    logger.info("Запуск миграций Django...")
    
    try:
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'migrate', '--noinput'])
        logger.info("Миграции успешно применены")
        return True
    except Exception as e:
        logger.error(f"Ошибка при применении миграций: {e}")
        return False


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Восстановление базы данных из JSON бэкапа')
    parser.add_argument('backup_file', help='Путь к файлу JSON бэкапа')
    parser.add_argument('--no-backup', action='store_true', help='Не создавать резервную копию текущей БД')
    parser.add_argument('--no-clear', action='store_true', help='Не очищать базу данных перед восстановлением')
    parser.add_argument('--no-migrate', action='store_true', help='Не запускать миграции Django после восстановления')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], help='Уровень логирования')
    parser.add_argument('--force', action='store_true', help='Принудительное восстановление без подтверждения')
    
    args = parser.parse_args()
    
    # Настройка логирования
    logger = setup_logging(args.log_level)
    
    try:
        # Проверка файла бэкапа
        backup_path = Path(args.backup_file)
        if not check_backup_file(backup_path):
            return 1
        
        # Загрузка JSON бэкапа
        backup_data = load_json_backup(backup_path)
        if not backup_data:
            return 1
        
        # Предупреждение о потере данных
        if not args.force:
            print("\n" + "="*60)
            print("ВНИМАНИЕ! Восстановление базы данных приведет к ПОЛНОЙ ПОТЕРЕ")
            print("всех текущих данных в базе данных!")
            print("="*60)
            
            response = input("Продолжить? (yes/no): ").lower().strip()
            if response not in ['yes', 'y', 'да', 'д']:
                logger.info("Операция отменена пользователем")
                return 0
        
        # Создание резервной копии текущей БД (если не отключено)
        if not args.no_backup:
            backup_dir = Path(settings.BASE_DIR) / 'backups'
            backup_dir.mkdir(exist_ok=True)
            
            current_backup = create_json_backup_before_restore(backup_dir)
            if not current_backup:
                logger.error("Не удалось создать резервную копию текущей БД")
                if not args.force:
                    response = input("Продолжить без резервной копии? (yes/no): ").lower().strip()
                    if response not in ['yes', 'y', 'да', 'д']:
                        return 1
        
        # Восстановление базы данных
        if not restore_json_backup(backup_data, not args.no_clear):
            logger.error("Не удалось восстановить базу данных")
            return 1
        
        # Запуск миграций (если не отключено)
        if not args.no_migrate:
            if not run_migrations():
                logger.warning("Ошибка при применении миграций, но восстановление завершено")
        
        logger.info("Восстановление базы данных успешно завершено!")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Операция прервана пользователем")
        return 1
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
