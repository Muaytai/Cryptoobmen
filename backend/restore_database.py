#!/usr/bin/env python3
"""
Скрипт для восстановления базы данных PostgreSQL из бэкапа
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
    
    log_file = log_dir / f'restore_{datetime.now().strftime("%Y%m%d")}.log'
    
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


def check_backup_file(backup_path):
    """Проверка существования и валидности файла бэкапа"""
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
    
    logger.info(f"Файл бэкапа найден: {backup_path}")
    logger.info(f"Размер файла: {file_size / (1024*1024):.2f} MB")
    
    return True


def create_database_backup_before_restore(backup_dir, db_config, compress=True):
    """Создание резервной копии текущей БД перед восстановлением"""
    logger = logging.getLogger(__name__)
    
    logger.warning("Создание резервной копии текущей базы данных...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"pre_restore_backup_{timestamp}"
    
    if compress:
        backup_filename += ".sql.gz"
        backup_path = backup_dir / backup_filename
    else:
        backup_filename += ".sql"
        backup_path = backup_dir / backup_filename
    
    # Формируем команду pg_dump
    env = os.environ.copy()
    env['PGPASSWORD'] = db_config['password']
    
    cmd = [
        'pg_dump',
        '-h', db_config['host'],
        '-p', str(db_config['port']),
        '-U', db_config['user'],
        '-d', db_config['name'],
        '--verbose',
        '--no-password',
        '--format=plain',
        '--encoding=UTF8',
        '--no-owner',
        '--no-privileges'
    ]
    
    try:
        if compress:
            with open(backup_path, 'wb') as f:
                process1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
                process2 = subprocess.Popen(['gzip'], stdin=process1.stdout, stdout=f, stderr=subprocess.PIPE)
                
                process1.stdout.close()
                stdout2, stderr2 = process2.communicate()
                
                if process2.returncode != 0:
                    raise subprocess.CalledProcessError(process2.returncode, 'gzip', stderr2)
                
                stdout1, stderr1 = process1.communicate()
                if process1.returncode != 0:
                    raise subprocess.CalledProcessError(process1.returncode, 'pg_dump', stderr1)
        else:
            with open(backup_path, 'w', encoding='utf-8') as f:
                process = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True
                )
                
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, 'pg_dump', process.stderr)
        
        logger.info(f"Резервная копия создана: {backup_path}")
        return backup_path
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при создании резервной копии: {e}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при создании резервной копии: {e}")
        return None


def drop_and_recreate_database(db_config):
    """Удаление и пересоздание базы данных"""
    logger = logging.getLogger(__name__)
    
    env = os.environ.copy()
    env['PGPASSWORD'] = db_config['password']
    
    # Подключение к postgres для удаления и создания БД
    admin_config = db_config.copy()
    admin_config['name'] = 'postgres'  # Подключаемся к системной БД
    
    logger.warning(f"Удаление базы данных: {db_config['name']}")
    
    # Удаление базы данных
    drop_cmd = [
        'psql',
        '-h', admin_config['host'],
        '-p', str(admin_config['port']),
        '-U', admin_config['user'],
        '-d', admin_config['name'],
        '-c', f'DROP DATABASE IF EXISTS "{db_config["name"]}";'
    ]
    
    try:
        process = subprocess.run(
            drop_cmd,
            env=env,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            logger.warning(f"Ошибка при удалении БД (возможно, БД не существует): {process.stderr}")
        else:
            logger.info("База данных успешно удалена")
    except Exception as e:
        logger.error(f"Ошибка при удалении БД: {e}")
        return False
    
    # Создание базы данных
    logger.info(f"Создание базы данных: {db_config['name']}")
    
    create_cmd = [
        'psql',
        '-h', admin_config['host'],
        '-p', str(admin_config['port']),
        '-U', admin_config['user'],
        '-d', admin_config['name'],
        '-c', f'CREATE DATABASE "{db_config["name"]}" WITH ENCODING "UTF8";'
    ]
    
    try:
        process = subprocess.run(
            create_cmd,
            env=env,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            logger.error(f"Ошибка при создании БД: {process.stderr}")
            return False
        
        logger.info("База данных успешно создана")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при создании БД: {e}")
        return False


def restore_database(backup_path, db_config, skip_db_creation=False):
    """Восстановление базы данных из бэкапа"""
    logger = logging.getLogger(__name__)
    
    env = os.environ.copy()
    env['PGPASSWORD'] = db_config['password']
    
    # Определяем, сжат ли файл
    is_compressed = backup_path.suffix == '.gz'
    
    logger.info(f"Восстановление базы данных из: {backup_path}")
    logger.info(f"Файл сжат: {is_compressed}")
    
    try:
        if is_compressed:
            # Восстановление из сжатого файла
            with open(backup_path, 'rb') as f:
                process1 = subprocess.Popen(['gunzip', '-c'], stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                cmd = [
                    'psql',
                    '-h', db_config['host'],
                    '-p', str(db_config['port']),
                    '-U', db_config['user'],
                    '-d', db_config['name'],
                    '-v', 'ON_ERROR_STOP=1'
                ]
                
                process2 = subprocess.Popen(
                    cmd,
                    stdin=process1.stdout,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True
                )
                
                process1.stdout.close()
                stdout2, stderr2 = process2.communicate()
                
                # Проверяем результат второго процесса (psql)
                if process2.returncode != 0:
                    logger.error(f"Ошибка при восстановлении БД: {stderr2}")
                    return False
                
                # Проверяем результат первого процесса (gunzip)
                stdout1, stderr1 = process1.communicate()
                if process1.returncode != 0:
                    logger.error(f"Ошибка при распаковке файла: {stderr1}")
                    return False
        else:
            # Восстановление из несжатого файла
            with open(backup_path, 'r', encoding='utf-8') as f:
                cmd = [
                    'psql',
                    '-h', db_config['host'],
                    '-p', str(db_config['port']),
                    '-U', db_config['user'],
                    '-d', db_config['name'],
                    '-v', 'ON_ERROR_STOP=1'
                ]
                
                process = subprocess.run(
                    cmd,
                    stdin=f,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True
                )
                
                if process.returncode != 0:
                    logger.error(f"Ошибка при восстановлении БД: {process.stderr}")
                    return False
        
        logger.info("База данных успешно восстановлена!")
        return True
        
    except Exception as e:
        logger.error(f"Неожиданная ошибка при восстановлении: {e}")
        return False


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
    parser = argparse.ArgumentParser(description='Восстановление базы данных PostgreSQL из бэкапа')
    parser.add_argument('backup_file', help='Путь к файлу бэкапа')
    parser.add_argument('--no-backup', action='store_true', help='Не создавать резервную копию текущей БД')
    parser.add_argument('--skip-db-creation', action='store_true', help='Не пересоздавать базу данных (только восстановление)')
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
        
        # Получение конфигурации БД
        db_config = get_db_config()
        logger.info(f"Подключение к БД: {db_config['host']}:{db_config['port']}/{db_config['name']}")
        
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
            
            current_backup = create_database_backup_before_restore(backup_dir, db_config)
            if not current_backup:
                logger.error("Не удалось создать резервную копию текущей БД")
                if not args.force:
                    response = input("Продолжить без резервной копии? (yes/no): ").lower().strip()
                    if response not in ['yes', 'y', 'да', 'д']:
                        return 1
        
        # Удаление и пересоздание базы данных (если не отключено)
        if not args.skip_db_creation:
            if not drop_and_recreate_database(db_config):
                logger.error("Не удалось пересоздать базу данных")
                return 1
        
        # Восстановление базы данных
        if not restore_database(backup_path, db_config, args.skip_db_creation):
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
