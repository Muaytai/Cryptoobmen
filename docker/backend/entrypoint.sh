#!/usr/bin/env sh
set -e

# Применяем миграции
python manage.py migrate --noinput

if [ "$DJANGO_ENV" = "production" ]; then
  echo "Starting Gunicorn (production)"
  exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120 --log-level info
else
  echo "Starting Django development server"
  exec python manage.py runserver 0.0.0.0:8000
fi
