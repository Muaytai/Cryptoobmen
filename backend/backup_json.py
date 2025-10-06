#!/usr/bin/env python3
"""
Скрипт для создания бэкапа базы данных в JSON формате
Использует Django ORM для экспорта данных
"""

import os
import sys
import json
import logging
import argparse
import gzip
from datetime import datetime, date, time
from pathlib import Path
from decimal import Decimal

# Добавляем путь к Django проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка Django окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.conf import settings
from django.core import serializers
from django.apps import apps


class DjangoJSONEncoder(json.JSONEncoder):
    """Кастомный JSON encoder для Django объектов"""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, time):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return super().default(obj)


def setup_logging(log_level='INFO'):
    """Настройка логирования"""
    log_dir = Path(settings.BASE_DIR) / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f'backup_json_{datetime.now().strftime("%Y%m%d")}.log'
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def create_backup_directory():
    """Создание директории для бэкапов"""
    backup_dir = Path(settings.BASE_DIR) / 'backups'
    backup_dir.mkdir(exist_ok=True)
    return backup_dir


def get_all_models():
    """Получение всех моделей Django"""
    models = []
    for app_config in apps.get_app_configs():
        models.extend(app_config.get_models())
    return models


def serialize_model_data(model, logger):
    """Сериализация данных модели в JSON"""
    try:
        objects = model.objects.all()
        count = objects.count()
        
        if count == 0:
            logger.info(f"Модель {model.__name__}: 0 объектов")
            return []
        
        logger.info(f"Сериализация модели {model.__name__}: {count} объектов")
        
        # Используем Django serializer для корректной сериализации
        serialized_data = serializers.serialize('python', objects)
        
        return {
            'model': f"{model._meta.app_label}.{model.__name__}",
            'count': count,
            'data': serialized_data
        }
        
    except Exception as e:
        logger.error(f"Ошибка при сериализации модели {model.__name__}: {e}")
        return None


def create_json_backup(backup_dir, compress=True, custom_name=None):
    """Создание JSON бэкапа"""
    logger = logging.getLogger(__name__)
    
    # Формируем имя файла бэкапа
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if custom_name:
        backup_filename = f"{custom_name}_{timestamp}"
    else:
        backup_filename = f"cryptoobmen_json_backup_{timestamp}"
    
    # Добавляем расширение в зависимости от сжатия
    if compress:
        backup_filename += ".json.gz"
        backup_path = backup_dir / backup_filename
    else:
        backup_filename += ".json"
        backup_path = backup_dir / backup_filename
    
    logger.info(f"Создание JSON бэкапа: {backup_filename}")
    
    try:
        # Получаем все модели
        models = get_all_models()
        logger.info(f"Найдено моделей для бэкапа: {len(models)}")
        
        # Создаем структуру бэкапа
        backup_data = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'django_version': django.get_version(),
                'database_engine': settings.DATABASES['default']['ENGINE'],
                'database_name': settings.DATABASES['default']['NAME'],
                'total_models': len(models)
            },
            'models': []
        }
        
        # Сериализуем данные каждой модели
        total_objects = 0
        for model in models:
            model_data = serialize_model_data(model, logger)
            if model_data:
                backup_data['models'].append(model_data)
                total_objects += model_data['count']
        
        backup_data['metadata']['total_objects'] = total_objects
        
        logger.info(f"Всего объектов для бэкапа: {total_objects}")
        
        # Сохраняем бэкап
        if compress:
            with gzip.open(backup_path, 'wt', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, cls=DjangoJSONEncoder)
        else:
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, cls=DjangoJSONEncoder)
        
        # Проверяем размер файла
        file_size = backup_path.stat().st_size
        logger.info(f"JSON бэкап успешно создан: {backup_path}")
        logger.info(f"Размер файла: {file_size / (1024*1024):.2f} MB")
        
        return backup_path
        
    except Exception as e:
        logger.error(f"Ошибка при создании JSON бэкапа: {e}")
        return None


def cleanup_old_backups(backup_dir, keep_days=7):
    """Удаление старых JSON бэкапов"""
    logger = logging.getLogger(__name__)
    
    if not backup_dir.exists():
        return
    
    cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
    removed_count = 0
    
    # Удаляем как .json, так и .json.gz файлы
    for pattern in ["*_json_backup_*.json*", "*_json_backup_*.json.gz"]:
        for backup_file in backup_dir.glob(pattern):
            if backup_file.stat().st_mtime < cutoff_date:
                try:
                    backup_file.unlink()
                    logger.info(f"Удален старый JSON бэкап: {backup_file.name}")
                    removed_count += 1
                except Exception as e:
                    logger.warning(f"Не удалось удалить {backup_file.name}: {e}")
    
    if removed_count > 0:
        logger.info(f"Удалено {removed_count} старых JSON бэкапов")


def list_json_backups(backup_dir):
    """Показать список существующих JSON бэкапов"""
    logger = logging.getLogger(__name__)
    
    if not backup_dir.exists():
        logger.info("Директория бэкапов не существует")
        return
    
    backups = []
    for pattern in ["*_json_backup_*.json*", "*_json_backup_*.json.gz"]:
        backups.extend(backup_dir.glob(pattern))
    
    if not backups:
        logger.info("JSON бэкапы не найдены")
        return
    
    logger.info(f"Найдено JSON бэкапов: {len(backups)}")
    logger.info("-" * 80)
    
    for backup in sorted(backups, key=lambda x: x.stat().st_mtime, reverse=True):
        file_size = backup.stat().st_size / (1024 * 1024)
        file_date = datetime.fromtimestamp(backup.stat().st_mtime)
        
        # Определяем, сжат ли файл
        is_compressed = backup.suffix == '.gz'
        compression_info = " (сжатый)" if is_compressed else " (несжатый)"
        
        logger.info(f"{backup.name:<60} {file_size:>8.2f} MB{compression_info}  {file_date.strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Создание JSON бэкапа базы данных')
    parser.add_argument('--name', '-n', help='Имя бэкапа (без расширения)')
    parser.add_argument('--no-compress', action='store_true', help='Не сжимать бэкап')
    parser.add_argument('--keep-days', type=int, default=7, help='Количество дней для хранения бэкапов (по умолчанию: 7)')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], help='Уровень логирования')
    parser.add_argument('--cleanup-only', action='store_true', help='Только очистить старые бэкапы')
    parser.add_argument('--list', action='store_true', help='Показать список существующих JSON бэкапов')
    
    args = parser.parse_args()
    
    # Настройка логирования
    logger = setup_logging(args.log_level)
    
    try:
        # Создание директории для бэкапов
        backup_dir = create_backup_directory()
        logger.info(f"Директория бэкапов: {backup_dir}")
        
        if args.list:
            # Показать список бэкапов
            list_json_backups(backup_dir)
            return 0
        
        if args.cleanup_only:
            # Только очистка старых бэкапов
            cleanup_old_backups(backup_dir, args.keep_days)
            logger.info("Очистка старых JSON бэкапов завершена")
            return 0
        
        # Создание JSON бэкапа
        backup_path = create_json_backup(
            backup_dir, 
            compress=not args.no_compress,
            custom_name=args.name
        )
        
        if backup_path:
            logger.info("JSON бэкап успешно создан!")
            
            # Очистка старых бэкапов
            cleanup_old_backups(backup_dir, args.keep_days)
            
            return 0
        else:
            logger.error("Не удалось создать JSON бэкап")
            return 1
            
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
