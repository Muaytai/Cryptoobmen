FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENV_FILE=.env

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
COPY docker/backend/.env.prod /app/.env


# Копирование исходного кода
COPY backend/ .

# Настройка разрешений
RUN mkdir -p /app/static /app/media && \
    chown -R app:app /app

# Сбор статических файлов для продакшена
ENV DEBUG=False
# Проверка, что переменные окружения загружены правильно
RUN echo "Проверка переменных окружения:" && \
    echo "ENV_FILE: $ENV_FILE" && \
    echo "SECRET_KEY exists: $(if [ -n "$SECRET_KEY" ]; then echo 'yes'; else echo 'no'; fi)" && \
    echo "DB_NAME: $DB_NAME" && \
    python -c "import os; print(f'Python читает SECRET_KEY: {os.getenv(\"SECRET_KEY\") is not None}')"
RUN python manage.py collectstatic --noinput

# Удаление временного .env файла
RUN rm -f /app/.env

# Переключение на непривилегированного пользователя
USER app

# Запуск gunicorn с указанным числом процессов

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]", "--timeout", "120"]





