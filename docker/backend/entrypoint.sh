#!/bin/sh
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

# Создаем необходимые директории с правильными правами через Python
# Это нужно, так как volume может быть смонтирован с правами root
echo "Creating required directories..."
python -c "
import os
import stat

dirs = [
    '/app/media/avatars',
    '/app/media/crypto_icons',
    '/app/logs/celery'
]

for dir_path in dirs:
    try:
        os.makedirs(dir_path, exist_ok=True)
        # Пытаемся установить права на запись для владельца
        try:
            os.chmod(dir_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)
        except PermissionError:
            pass  # Игнорируем, если нет прав на изменение
        print(f'Directory {dir_path} ready')
    except PermissionError as e:
        print(f'Warning: Cannot create {dir_path}: {e}')
        print('You may need to fix volume permissions manually')
" || echo "Directory creation completed (some may have failed)"

# Выполняем миграции и сбор статических файлов (только для продакшена)
# Проверяем, не является ли это командой celery
if echo "$@" | grep -qv "celery"; then
    echo "Running migrations..."
    python manage.py migrate --noinput || echo "Migration failed, continuing..."
    
    echo "Updating Site configuration..."
    python manage.py shell << EOF || echo "Site update failed, continuing..."
from django.contrib.sites.models import Site
from django.conf import settings
from urllib.parse import urlparse

# Получаем домен из FRONTEND_URL
frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
parsed = urlparse(frontend_url)
domain = parsed.netloc or parsed.path.replace('http://', '').replace('https://', '').strip('/')
if not domain:
    domain = 'tkxn.org'

# Обновляем или создаем запись Site с ID=2
site, created = Site.objects.update_or_create(
    id=2,
    defaults={
        'domain': domain,
        'name': 'TokenX'
    }
)
print(f"Site {'created' if created else 'updated'}: {site.domain} ({site.name})")
EOF
    
    echo "Collecting static files..."
    python manage.py collectstatic --noinput || echo "Collectstatic failed, continuing..."
fi

# Запускаем команду, переданную в docker-compose
echo "Executing command: $@"
exec "$@"
