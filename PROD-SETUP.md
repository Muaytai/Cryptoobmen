# Настройка продакшен-окружения для Cryptoobmen

## Обзор

Продакшен-окружение состоит из следующих компонентов:
- **База данных PostgreSQL** - Хранит все данные приложения
- **Redis** - Используется для кэширования и очередей
- **Бэкенд на Django** - API и админ-панель
- **Фронтенд на Next.js** - Клиентское приложение
- **Nginx** - Веб-сервер для проксирования запросов и обслуживания статических файлов

## Структура файлов

```
project_root/
├── docker/
│   ├── backend/
│   │   ├── .env.prod      # Переменные окружения для бэкенда
│   │   └── Dockerfile     # Dockerfile для бэкенда
│   ├── frontend/
│   │   ├── .env.prod      # Переменные окружения для фронтенда
│   │   └── Dockerfile     # Dockerfile для фронтенда
│   ├── nginx/
│   │   ├── conf.d/        # Конфигурация Nginx
│   │   │   └── cryptoobmen.conf
│   │   └── Dockerfile     # Dockerfile для Nginx
│   └── postgres/
│       ├── .env.prod      # Переменные окружения для PostgreSQL
│       └── docker-compose.db.yml # Compose для запуска БД и Redis
├── docker-compose.prod.yml # Основной файл Compose для продакшена
├── start-prod.ps1          # Скрипт запуска продакшен-окружения (Windows)
├── stop-prod.ps1           # Скрипт остановки продакшен-окружения (Windows)
├── start-prod.sh           # Скрипт запуска продакшен-окружения (Linux)
└── stop-prod.sh            # Скрипт остановки продакшен-окружения (Linux)
```

## Подготовка к запуску

1. Убедитесь, что файлы `.env.prod` содержат актуальные данные:
   - `docker/backend/.env.prod` - настройки Django, базы данных и почты
   - `docker/frontend/.env.prod` - настройки фронтенда и URL API
   - `docker/postgres/.env.prod` - учетные данные для PostgreSQL

2. Проверьте настройки Nginx в файле `docker/nginx/conf.d/cryptoobmen.conf`:
   - Убедитесь, что `server_name` соответствует вашему домену или IP-адресу
   - Раскомментируйте SSL-секцию, если вы настраиваете HTTPS

## Запуск продакшен-окружения

### Windows

#### Вариант 1: Использование скрипта

Запустите скрипт PowerShell:

```powershell
./start-prod.ps1
```

#### Вариант 2: Ручной запуск

Если вы предпочитаете запускать контейнеры вручную:

1. Сначала запустите базу данных и Redis:
   ```powershell
   cd docker/postgres
   docker-compose -f docker-compose.db.yml up -d
   cd ../..
   ```

2. Затем запустите основные сервисы:
   ```powershell
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Linux

#### Вариант 1: Использование скрипта

Сделайте скрипт исполняемым и запустите его:

```bash
chmod +x start-prod.sh
./start-prod.sh
```

#### Вариант 2: Ручной запуск

Если вы предпочитаете запускать контейнеры вручную:

1. Сначала запустите базу данных и Redis:
   ```bash
   cd docker/postgres
   docker-compose -f docker-compose.db.yml up -d
   cd ../..
   ```

2. Затем запустите основные сервисы:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Проверка работы

После запуска все сервисы должны быть доступны:

- **Веб-сайт**: http://194.15.46.70 (или ваш домен)
- **Админ-панель Django**: http://194.15.46.70/admin/
- **API**: http://194.15.46.70/api/

## Остановка продакшен-окружения

### Windows

#### Вариант 1: Использование скрипта

```powershell
./stop-prod.ps1
```

#### Вариант 2: Ручной останов

```powershell
docker-compose -f docker-compose.prod.yml down
cd docker/postgres
docker-compose -f docker-compose.db.yml down
```

### Linux

#### Вариант 1: Использование скрипта

```bash
chmod +x stop-prod.sh
./stop-prod.sh
```

#### Вариант 2: Ручной останов

```bash
docker-compose -f docker-compose.prod.yml down
cd docker/postgres
docker-compose -f docker-compose.db.yml down
```

## Обслуживание и мониторинг

### Просмотр логов

```bash
# Логи бэкенда
docker logs cryptoobmen-backend

# Логи фронтенда
docker logs cryptoobmen-frontend

# Логи Nginx
docker logs cryptoobmen-nginx

# Логи базы данных
docker logs cryptoobmen-postgres
```

### Резервное копирование базы данных

```bash
# В Linux
docker exec cryptoobmen-postgres pg_dump -U postgres cryptoobmen > backup_$(date +%Y%m%d).sql

# В Windows
docker exec cryptoobmen-postgres pg_dump -U postgres cryptoobmen > backup_$(Get-Date -Format "yyyyMMdd").sql
```

## Устранение неполадок

### Проблемы с подключением к базе данных

1. Проверьте, что контейнер базы данных запущен:
   ```bash
   docker ps | grep postgres
   ```

2. Проверьте настройки подключения в `.env.prod` файлах

### Проблемы с Nginx

1. Проверьте логи Nginx:
   ```bash
   docker logs cryptoobmen-nginx
   ```

2. Убедитесь, что конфигурация в `cryptoobmen.conf` корректна

### Команды Docker Compose в Linux

В зависимости от версии Docker Compose в Linux, вам может потребоваться использовать:

- Для Docker Compose V1: `docker-compose`
- Для Docker Compose V2: `docker compose` (без дефиса)

Проверьте версию с помощью команды `docker-compose --version` или `docker compose version` и используйте соответствующий синтаксис в командах и скриптах. 