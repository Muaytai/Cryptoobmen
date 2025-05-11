# Локальная среда разработки

Эта папка содержит настройки Docker для локальной разработки проекта Cryptoobmen.

## Запуск

Для запуска локальной среды разработки выполните:

```bash
# Из папки docker/local
docker-compose -f docker-compose.local.yml up -d

# Или из корня проекта
docker-compose -f docker/local/docker-compose.local.yml up -d
```

## Особенности локального окружения

1. **Горячая перезагрузка кода**:
   - При изменении файлов в папке `backend/` изменения автоматически применяются к работающему контейнеру Django
   - При изменении файлов в папке `frontend/` изменения автоматически применяются к работающему контейнеру Next.js

2. **Доступные сервисы**:
   - Django backend: http://localhost:8000
   - Django admin: http://localhost:8000/admin
   - Next.js frontend: http://localhost:3000
   - PostgreSQL: localhost:5432 (для подключения из IDE или других инструментов)
   - Redis: localhost:6379

3. **Настройки по умолчанию**:
   - PostgreSQL:
     - Database: cryptoobmen
     - User: postgres
     - Password: postgres
   - Django:
     - Debug mode: включен
     - Admin: создайте суперпользователя командой `docker-compose exec backend python manage.py createsuperuser`

## Полезные команды

```bash
# Запуск сервисов
docker-compose -f docker-compose.local.yml up -d

# Остановка сервисов
docker-compose -f docker-compose.local.yml down

# Перезапуск конкретного сервиса
docker-compose -f docker-compose.local.yml restart backend

# Просмотр логов всех сервисов
docker-compose -f docker-compose.local.yml logs -f

# Просмотр логов конкретного сервиса
docker-compose -f docker-compose.local.yml logs -f backend

# Выполнение миграций Django
docker-compose -f docker-compose.local.yml exec backend python manage.py migrate

# Создание суперпользователя Django
docker-compose -f docker-compose.local.yml exec backend python manage.py createsuperuser
``` 