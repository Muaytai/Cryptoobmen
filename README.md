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

#### 1. Клонировать репозиторий

```bash
git clone https://github.com/Muaytai/Cryptoobmen.git
cd Cryptoobmen
```

#### 2. Создать файлы окружения

Создайте файлы .env в соответствующих директориях:

**backend/.env**:
```
SECRET_KEY=secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_ENGINE=django.db.backends.postgresql
DB_NAME=cryptoobmen
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=postgres
DB_PORT=5432
```

**frontend/.env**:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

**postgres/.env**:
```
POSTGRES_DB=cryptoobmen
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

#### 3. Запустить с Docker Compose

```bash
# Создать образы
docker compose build

# Запустить контейнеры
docker compose up -d

# Применить миграции
docker compose exec backend python manage.py migrate

# Создать суперпользователя
docker compose exec backend python manage.py createsuperuser
```

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

#### На Linux/macOS:
```bash
# Сделайте скрипт исполняемым
chmod +x deploy.sh

# Запустите скрипт деплоя
./deploy.sh
```

#### На Windows:
```powershell
# Запустите скрипт деплоя
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
