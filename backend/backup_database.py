#!/usr/bin/env python3
"""
Скрипт для создания бэкапа базы данных PostgreSQL
Использует настройки из Django settings.py
"""

import os
import sys
import subprocess
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Добавляем путь к Django проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка Django окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.conf import settings


def setup_logging(log_level='INFO'):
    """Настройка логирования"""
    log_dir = Path(settings.BASE_DIR) / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f'backup_{datetime.now().strftime("%Y%m%d")}.log'
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def get_db_config():
    """Получение конфигурации базы данных"""
    db_config = settings.DATABASES['default']
    return {
        'host': db_config['HOST'],
        'port': db_config['PORT'],
        'name': db_config['NAME'],
        'user': db_config['USER'],
        'password': db_config['PASSWORD']
    }


def create_backup_directory():
    """Создание директории для бэкапов"""
    backup_dir = Path(settings.BASE_DIR) / 'backups'
    backup_dir.mkdir(exist_ok=True)
    return backup_dir


def create_database_backup(backup_dir, db_config, compress=True, custom_name=None):
    """Создание бэкапа базы данных"""
    logger = logging.getLogger(__name__)
    
    # Формируем имя файла бэкапа
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if custom_name:
        backup_filename = f"{custom_name}_{timestamp}"
    else:
        backup_filename = f"cryptoobmen_backup_{timestamp}"
    
    # Добавляем расширение в зависимости от сжатия
    if compress:
        backup_filename += ".sql.gz"
        backup_path = backup_dir / backup_filename
    else:
        backup_filename += ".sql"
        backup_path = backup_dir / backup_filename
    
    logger.info(f"Создание бэкапа базы данных: {backup_filename}")
    
    # Формируем команду pg_dump
    env = os.environ.copy()
    env['PGPASSWORD'] = db_config['password']
    
    cmd = [
        'pg_dump',
        '-h', db_config['host'],
        '-p', str(db_config['port']),
        '-U', db_config['user'],
        '-d', db_config['name'],
        '--no-password',
        '--format=plain',
        '--encoding=UTF8'
    ]
    
    try:
        if compress:
            # Создаем сжатый бэкап
            with open(backup_path, 'wb') as f:
                process1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
                process2 = subprocess.Popen(['gzip'], stdin=process1.stdout, stdout=f, stderr=subprocess.PIPE)
                
                process1.stdout.close()
                stdout2, stderr2 = process2.communicate()
                
                # Проверяем результат второго процесса
                if process2.returncode != 0:
                    raise subprocess.CalledProcessError(process2.returncode, 'gzip', stderr2)
                
                # Проверяем результат первого процесса
                stdout1, stderr1 = process1.communicate()
                if process1.returncode != 0:
                    error_msg = stderr1.decode() if stderr1 else 'No error message'
                    raise subprocess.CalledProcessError(process1.returncode, 'pg_dump', error_msg)
        else:
            # Создаем несжатый бэкап
            with open(backup_path, 'w', encoding='utf-8') as f:
                process = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True
                )
                
                if process.returncode != 0:
                    error_msg = process.stderr if process.stderr else 'No error message'
                    raise subprocess.CalledProcessError(process.returncode, 'pg_dump', error_msg)
        
        # Проверяем размер файла
        file_size = backup_path.stat().st_size
        logger.info(f"Бэкап успешно создан: {backup_path}")
        logger.info(f"Размер файла: {file_size / (1024*1024):.2f} MB")
        
        return backup_path
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при создании бэкапа: {e}")
        logger.error(f"Stderr: {e.stderr.decode() if e.stderr else 'N/A'}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return None


def cleanup_old_backups(backup_dir, keep_days=7):
    """Удаление старых бэкапов"""
    logger = logging.getLogger(__name__)
    
    if not backup_dir.exists():
        return
    
    cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
    removed_count = 0
    
    for backup_file in backup_dir.glob("*.sql*"):
        if backup_file.stat().st_mtime < cutoff_date:
            try:
                backup_file.unlink()
                logger.info(f"Удален старый бэкап: {backup_file.name}")
                removed_count += 1
            except Exception as e:
                logger.warning(f"Не удалось удалить {backup_file.name}: {e}")
    
    if removed_count > 0:
        logger.info(f"Удалено {removed_count} старых бэкапов")


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Создание бэкапа базы данных PostgreSQL')
    parser.add_argument('--name', '-n', help='Имя бэкапа (без расширения)')
    parser.add_argument('--no-compress', action='store_true', help='Не сжимать бэкап')
    parser.add_argument('--keep-days', type=int, default=7, help='Количество дней для хранения бэкапов (по умолчанию: 7)')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], help='Уровень логирования')
    parser.add_argument('--cleanup-only', action='store_true', help='Только очистить старые бэкапы')
    
    args = parser.parse_args()
    
    # Настройка логирования
    logger = setup_logging(args.log_level)
    
    try:
        # Получение конфигурации БД
        db_config = get_db_config()
        logger.info(f"Подключение к БД: {db_config['host']}:{db_config['port']}/{db_config['name']}")
        
        # Создание директории для бэкапов
        backup_dir = create_backup_directory()
        logger.info(f"Директория бэкапов: {backup_dir}")
        
        if args.cleanup_only:
            # Только очистка старых бэкапов
            cleanup_old_backups(backup_dir, args.keep_days)
            logger.info("Очистка старых бэкапов завершена")
            return 0
        
        # Создание бэкапа
        backup_path = create_database_backup(
            backup_dir, 
            db_config, 
            compress=not args.no_compress,
            custom_name=args.name
        )
        
        if backup_path:
            logger.info("Бэкап успешно создан!")
            
            # Очистка старых бэкапов
            cleanup_old_backups(backup_dir, args.keep_days)
            
            return 0
        else:
            logger.error("Не удалось создать бэкап")
            return 1
            
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
