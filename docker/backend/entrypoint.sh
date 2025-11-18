#!/usr/bin/env sh
set -e

# Ждем доступности базы данных
echo "Waiting for database..."
export DJANGO_SETTINGS_MODULE=core.settings
python -c "
import sys
import time
import psycopg2
import os

# Получаем параметры подключения из переменных окружения
dbname = os.environ.get('POSTGRES_DB')
user = os.environ.get('POSTGRES_USER')
password = os.environ.get('POSTGRES_PASSWORD')
host = os.environ.get('POSTGRES_HOST', 'postgres')  # По умолчанию используем имя сервиса в Docker
port = os.environ.get('POSTGRES_PORT', '5432')

print(f'Trying to connect to PostgreSQL at {host}:{port}...')

# Максимальное время ожидания в секундах
max_wait = 60
start_time = time.time()

while True:
    try:
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.close()
        print('Database is available!')
        break
    except Exception as e:
        elapsed = time.time() - start_time
        if elapsed > max_wait:
            print(f'Database connection error: {e}')
            sys.exit(1)
        print(f'Waiting for database... {int(elapsed)}s')
        time.sleep(2)
"

# Выполняем миграции и сбор статических файлов (только для продакшена)
# Проверяем, не является ли это командой celery
if echo "$@" | grep -qv "celery"; then
    echo "Running migrations..."
    python manage.py migrate --noinput || echo "Migration failed, continuing..."
    
    echo "Collecting static files..."
    python manage.py collectstatic --noinput || echo "Collectstatic failed, continuing..."
fi

# Запускаем команду, переданную в docker-compose
echo "Executing command: $@"
exec "$@"
