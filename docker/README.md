# Docker конфигурация для Cryptoobmen

## Структура

- `docker-compose.yml` - конфигурация для продакшена
- `docker/docker-compose.dev.yml` - конфигурация для разработки
- `docker/postgres/docker-compose.db.yml` - отдельная конфигурация для базы данных

## Локальный запуск (разработка)

1. Создайте сеть Docker (если еще не создана):
```bash
docker network create cryptoobmen_network
```

2. Запустите базу данных:
```bash
cd docker/postgres
docker compose -f docker-compose.db.yml up -d
```

3. Запустите все сервисы для разработки:
```bash
cd docker
docker compose -f docker-compose.dev.yml up --build
```

Сервисы будут доступны:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Продакшен запуск

1. Убедитесь, что создана сеть:
```bash
docker network create cryptoobmen_network
```

2. Запустите все сервисы:
```bash
docker compose up -d --build
```

Сервисы будут доступны через nginx на портах 80 и 443.

## Сервисы

### Продакшен (docker-compose.yml)
- **nginx** - веб-сервер и reverse proxy
- **backend** - Django приложение (Gunicorn + Uvicorn)
- **frontend** - Next.js приложение
- **postgres** - база данных PostgreSQL
- **redis** - кэш и брокер сообщений для Celery
- **worker** - Celery worker для фоновых задач
- **beat** - Celery beat для периодических задач

### Разработка (docker/docker-compose.dev.yml)
- **postgres** - база данных PostgreSQL
- **redis** - кэш и брокер сообщений
- **backend** - Django с hot-reload (Uvicorn)
- **frontend** - Next.js с hot-reload
- **worker** - Celery worker (pool=solo для разработки)
- **beat** - Celery beat

## Переменные окружения

Убедитесь, что файлы `.env.backend` и `.env.development` / `.env.production` настроены правильно.

## Volumes

- `static_volume` - статические файлы Django
- `media_volume` - медиа файлы
- `postgres_data` / `postgres_data_dev` - данные PostgreSQL

## Healthchecks

Все сервисы имеют healthchecks для правильной инициализации зависимостей:
- PostgreSQL проверяется через `pg_isready`
- Redis проверяется через `redis-cli ping`
- Backend проверяется через socket соединение
- Frontend проверяется через HTTP запрос
- Nginx проверяется через curl

## Примечания

- В продакшене миграции и collectstatic выполняются автоматически при запуске backend через entrypoint.sh
- В разработке используется hot-reload для быстрой итерации
- Worker и Beat зависят от backend, postgres и redis
- Nginx зависит от backend и frontend с условием service_healthy

