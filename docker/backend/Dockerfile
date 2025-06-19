FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENV_FILE=.env.prod

# Установка зависимостей
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    musl-dev \
    gettext \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя без прав администратора
RUN addgroup --system app && adduser --system --group app

# Рабочая директория
WORKDIR /app

# Копирование и установка зависимостей отдельно для кэширования слоев
COPY backend/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn

# Копирование .env файла для продакшена
COPY docker/backend/.env.prod /app/.env.prod

# Копирование entrypoint
COPY docker/backend/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Копирование исходного кода
COPY backend/ .

# Настройка разрешений и создание директорий
RUN mkdir -p /app/static /app/media && \
    mkdir -p /app/logs && \
    touch /app/logs/django.log && \
    chown -R app:app /app

# Выполнение сбора статических файлов для продакшена
ENV DEBUG=False
RUN python manage.py collectstatic --noinput

# Переключение на непривилегированного пользователя

ENTRYPOINT ["/app/entrypoint.sh"]

# Переключение на непривилегированного пользователя
USER app







