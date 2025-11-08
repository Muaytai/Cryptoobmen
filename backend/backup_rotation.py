#!/usr/bin/env python3
"""
Скрипт для автоматического создания бэкапов с ротацией
Поддерживает различные стратегии хранения бэкапов
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Добавляем путь к Django проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка Django окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.conf import settings


def setup_logging():
    """Настройка логирования"""
    log_dir = Path(settings.BASE_DIR) / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f'backup_rotation_{datetime.now().strftime("%Y%m%d")}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def create_backup_with_strategy(strategy='daily', custom_name=None):
    """Создание бэкапа с определенной стратегией именования"""
    logger = logging.getLogger(__name__)
    
    now = datetime.now()
    backup_name = None
    
    if strategy == 'daily':
        backup_name = f"daily_{now.strftime('%Y%m%d')}"
    elif strategy == 'weekly':
        # Определяем номер недели в году
        week_num = now.isocalendar()[1]
        backup_name = f"weekly_{now.year}_W{week_num:02d}"
    elif strategy == 'monthly':
        backup_name = f"monthly_{now.strftime('%Y%m')}"
    elif strategy == 'yearly':
        backup_name = f"yearly_{now.year}"
    elif custom_name:
        backup_name = custom_name
    else:
        backup_name = f"backup_{now.strftime('%Y%m%d_%H%M%S')}"
    
    logger.info(f"Создание бэкапа по стратегии '{strategy}': {backup_name}")
    
    # Импортируем функцию создания бэкапа
    from backup_database import create_backup_directory, get_db_config, create_database_backup
    
    try:
        db_config = get_db_config()
        backup_dir = create_backup_directory()
        
        backup_path = create_database_backup(
            backup_dir, 
            db_config, 
            compress=True,
            custom_name=backup_name
        )
        
        if backup_path:
            logger.info(f"Бэкап успешно создан: {backup_path}")
            return backup_path
        else:
            logger.error("Не удалось создать бэкап")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка при создании бэкапа: {e}")
        return None


def cleanup_old_backups_by_strategy(backup_dir, strategy='daily'):
    """Очистка старых бэкапов по стратегии"""
    logger = logging.getLogger(__name__)
    
    if not backup_dir.exists():
        return
    
    removed_count = 0
    now = datetime.now()
    
    if strategy == 'daily':
        # Храним последние 7 дней
        cutoff_date = now - timedelta(days=7)
        pattern = "daily_*.sql.gz"
        
    elif strategy == 'weekly':
        # Храним последние 4 недели
        cutoff_date = now - timedelta(weeks=4)
        pattern = "weekly_*.sql.gz"
        
    elif strategy == 'monthly':
        # Храним последние 12 месяцев
        cutoff_date = now - timedelta(days=365)
        pattern = "monthly_*.sql.gz"
        
    elif strategy == 'yearly':
        # Храним последние 3 года
        cutoff_date = now - timedelta(days=3*365)
        pattern = "yearly_*.sql.gz"
        
    else:
        # По умолчанию храним 7 дней
        cutoff_date = now - timedelta(days=7)
        pattern = "*.sql.gz"
    
    logger.info(f"Очистка старых бэкапов по стратегии '{strategy}'")
    
    for backup_file in backup_dir.glob(pattern):
        try:
            file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            if file_mtime < cutoff_date:
                backup_file.unlink()
                logger.info(f"Удален старый бэкап: {backup_file.name}")
                removed_count += 1
        except Exception as e:
            logger.warning(f"Не удалось удалить {backup_file.name}: {e}")
    
    if removed_count > 0:
        logger.info(f"Удалено {removed_count} старых бэкапов")
    else:
        logger.info("Старые бэкапы не найдены для удаления")


def list_backups(backup_dir, strategy=None):
    """Показать список существующих бэкапов"""
    logger = logging.getLogger(__name__)
    
    if not backup_dir.exists():
        logger.info("Директория бэкапов не существует")
        return
    
    pattern = f"{strategy}_*.sql.gz" if strategy else "*.sql.gz"
    backups = list(backup_dir.glob(pattern))
    
    if not backups:
        logger.info(f"Бэкапы не найдены (паттерн: {pattern})")
        return
    
    logger.info(f"Найдено бэкапов: {len(backups)}")
    logger.info("-" * 80)
    
    for backup in sorted(backups, key=lambda x: x.stat().st_mtime, reverse=True):
        file_size = backup.stat().st_size / (1024 * 1024)
        file_date = datetime.fromtimestamp(backup.stat().st_mtime)
        logger.info(f"{backup.name:<50} {file_size:>8.2f} MB  {file_date.strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Автоматическое создание бэкапов с ротацией')
    parser.add_argument('--strategy', choices=['daily', 'weekly', 'monthly', 'yearly'], 
                       default='daily', help='Стратегия создания бэкапов')
    parser.add_argument('--name', help='Кастомное имя бэкапа')
    parser.add_argument('--list', action='store_true', help='Показать список существующих бэкапов')
    parser.add_argument('--cleanup-only', action='store_true', help='Только очистить старые бэкапы')
    parser.add_argument('--no-cleanup', action='store_true', help='Не очищать старые бэкапы')
    
    args = parser.parse_args()
    
    # Настройка логирования
    logger = setup_logging()
    
    try:
        from backup_database import create_backup_directory
        backup_dir = create_backup_directory()
        
        if args.list:
            # Показать список бэкапов
            list_backups(backup_dir, args.strategy if not args.name else None)
            return 0
        
        if args.cleanup_only:
            # Только очистка
            cleanup_old_backups_by_strategy(backup_dir, args.strategy)
            return 0
        
        # Создание бэкапа
        backup_path = create_backup_with_strategy(args.strategy, args.name)
        
        if backup_path:
            logger.info("Бэкап успешно создан!")
            
            # Очистка старых бэкапов (если не отключено)
            if not args.no_cleanup:
                cleanup_old_backups_by_strategy(backup_dir, args.strategy)
            
            return 0
        else:
            logger.error("Не удалось создать бэкап")
            return 1
            
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
