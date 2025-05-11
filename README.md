# Crypto Exchange Platform

Платформа для обмена криптовалют с современным интерфейсом и безопасной авторизацией.

## Структура проекта

- `backend/` - Django REST Framework бэкенд
- `frontend/` - Next.js фронтенд
- `postgres/` - PostgreSQL
- `docker/` - Docker-конфигурации для продакшена

## Технологии

- Backend: Django, Django REST Framework, JWT
- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Авторизация: django-allauth, next-auth
- Контейнеризация: Docker, Docker Compose

## Локальная разработка

Для локальной разработки есть два варианта: с использованием Docker или без него.

### Вариант 1: Быстрый старт (без Docker)

Для быстрого старта используйте скрипты настройки:

#### Windows:
```bash
# Запускает автоматическую настройку
.\setup.bat
```

#### Linux/macOS:
```bash
# Делаем скрипт исполняемым
chmod +x setup.sh

# Запускаем автоматическую настройку
./setup.sh
```

После настройки можно запустить:
- Бэкенд: `cd backend && venv\Scripts\activate && python manage.py runserver`
- Фронтенд: `cd frontend && npm run dev`

### Вариант 2: Локальная разработка с Docker

```bash
# Запуск локальной среды разработки
docker-compose -f docker/local/docker-compose.local.yml up -d

# Создание суперпользователя Django (опционально)
docker-compose -f docker/local/docker-compose.local.yml exec backend python manage.py createsuperuser
```

После запуска доступны:
- Django backend: http://localhost:8000
- Django admin: http://localhost:8000/admin
- Next.js frontend: http://localhost:3000

Более подробные инструкции смотрите в [docker/local/README.md](docker/local/README.md)

## Деплой на продакшен-сервер

### Подготовка к деплою

1. Клонируйте репозиторий на сервер:
   ```bash
   git clone <url-репозитория> cryptoobmen
   cd cryptoobmen
   ```

2. Создайте файлы с переменными окружения на основе примеров:
   ```bash
   # Для PostgreSQL
   cp docker/postgres/example.env.prod docker/postgres/.env.prod
   
   # Для бэкенда (Django)
   cp docker/backend/example.env.prod docker/backend/.env.prod
   
   # Для фронтенда (Next.js)
   cp docker/frontend/example.env.prod docker/frontend/.env.prod
   ```

3. Отредактируйте файлы .env.prod, установив безопасные пароли и другие настройки

### Запуск деплоя

#### Вариант 1: Раздельный запуск базы данных и приложения (рекомендуется)

1. Сначала запустите только базу данных и Redis:
```bash
# На Linux/macOS
cd docker/postgres
docker-compose -f docker-compose.db.yml up -d

# На Windows
cd docker\postgres
docker-compose -f docker-compose.db.yml up -d
```

2. Затем запустите основные сервисы (в корне проекта):
```bash
# На Linux/macOS
cd ../..  # Вернуться в корень проекта
docker-compose -f docker-compose.prod.yml up -d

# На Windows
cd ..\..  # Вернуться в корень проекта
docker-compose -f docker-compose.prod.yml up -d
```

3. Применить миграции и создать суперпользователя:
```bash
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

#### Вариант 2: Запуск всех сервисов вместе

```bash
# На Linux/macOS
chmod +x deploy.sh
./deploy.sh

# На Windows
.\deploy.ps1
```

### Что делает скрипт деплоя:

1. Проверяет наличие всех необходимых .env.prod файлов
2. Собирает Docker-образы с помощью docker-compose
3. Запускает контейнеры в фоновом режиме
4. Выполняет миграции Django
5. Предлагает создать суперпользователя (опционально)

### Структура Docker-контейнеров:

- **postgres**: База данных PostgreSQL
- **redis**: Redis для кэширования/очередей
- **backend**: Django REST Framework API
- **frontend**: Next.js фронтенд
- **nginx**: Веб-сервер, который проксирует запросы к бэкенду и фронтенду

### SSL-сертификат (после деплоя):

Для настройки HTTPS выполните следующие шаги:

1. Получите SSL-сертификат (например, с помощью Let's Encrypt)
2. Поместите сертификаты в директорию `docker/nginx/ssl/`
3. Раскомментируйте секцию HTTPS в `docker/nginx/conf.d/cryptoobmen.conf`
4. Перезапустите контейнер nginx:
   ```bash
   docker-compose -f docker-compose.prod.yml restart nginx
   ```

### Мониторинг логов:

```bash
# Мониторинг логов всех контейнеров
docker-compose -f docker-compose.prod.yml logs -f

# Мониторинг логов конкретного контейнера
docker-compose -f docker-compose.prod.yml logs -f backend
```

## Возможности

- Светлая и темная тема интерфейса
- Авторизация через Google, Yandex, Telegram
- Личный кабинет пользователя
- Удобная система обмена криптовалют
- Просмотр истории транзакций
