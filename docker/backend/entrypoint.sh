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
dbname = os.environ.get('POSTGRES_DB', 'cryptoobmen')
user = os.environ.get('POSTGRES_USER', 'postgres')
password = os.environ.get('POSTGRES_PASSWORD', 'postgres')
host = os.environ.get('POSTGRES_HOST', 'cryptoobmen-postgres')
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

# Применяем миграции
python manage.py migrate --noinput

if [ "$DJANGO_ENV" = "production" ]; then
  echo "Starting Gunicorn (production)"
  exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120 --log-level info
else
  echo "Starting Django development server"
  exec python manage.py runserver 0.0.0.0:8000
fi
