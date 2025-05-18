# Cryptoobmen

Проект обмена криптовалют, разработанный с использованием Django REST Framework (backend) и Next.js (frontend).

## Содержание

- [Настройка окружения](#настройка-окружения)
- [Локальная разработка](#локальная-разработка)
- [Docker разработка](#docker-разработка)
- [Проблемы гидратации Next.js](#проблемы-гидратации-nextjs)
- [Деплой](#деплой)

## Настройка окружения

### Требования

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- PowerShell (для Windows)

### Настройка для Windows

```powershell
# Клонирование репозитория
git clone https://your-repo-url/cryptoobmen.git
cd cryptoobmen

# Проверка установленных версий
python --version
node --version
docker --version
docker-compose --version
```

## Локальная разработка

### Backend (Django)

```powershell
# Перейти в директорию backend
cd backend

# Создать виртуальное окружение
python -m venv venv
.\venv\Scripts\Activate

# Установить зависимости
pip install -r requirements.txt

# Запустить миграции
python manage.py migrate

# Создать суперпользователя
python manage.py createsuperuser

# Запустить сервер разработки
python manage.py runserver
```

### Frontend (Next.js)

```powershell
# Перейти в директорию frontend
cd frontend

# Установить зависимости
npm install

# Запустить сервер разработки
npm run dev

# Собрать для production
npm run build

# Запустить production версию
npm run start
```

## Docker разработка

### Запуск всех сервисов

```powershell
# Из корневой директории проекта
.\docker\local\start-local.ps1

# Если скрипт не работает, можно запустить вручную:
cd docker\local
docker-compose -f docker-compose.local.yml up -d
```

### Остановка контейнеров

```powershell
# Из директории docker\local
docker-compose -f docker-compose.local.yml down

# Или из корневой директории
docker-compose -f .\docker\local\docker-compose.local.yml down
```

### Просмотр логов

```powershell
# Все логи
docker-compose -f .\docker\local\docker-compose.local.yml logs -f

# Логи конкретного сервиса
docker-compose -f .\docker\local\docker-compose.local.yml logs -f frontend
docker-compose -f .\docker\local\docker-compose.local.yml logs -f backend
```

### Перезапуск отдельных сервисов

```powershell
# Перезапуск фронтенда
docker-compose -f .\docker\local\docker-compose.local.yml restart frontend

# Перезапуск бэкенда
docker-compose -f .\docker\local\docker-compose.local.yml restart backend
```

## Проблемы гидратации Next.js

В проекте реализовано несколько решений для устранения проблем гидратации Next.js, особенно связанных с атрибутами `bls_skin_checked="1"`, добавляемыми расширениями браузера.

### Проверка наличия проблем гидратации

```powershell
# Запуск frontend в режиме разработки
cd frontend
npm run dev

# Затем откройте консоль разработчика в браузере (F12)
# Ищите предупреждения вида "Warning: Prop `className` did not match..."
```

### Решения для проблем гидратации

В проекте реализованы следующие компоненты:

1. **HydrationFix** - удаляет проблемные атрибуты, добавляемые расширениями браузера
2. **ClientOnly** - рендерит содержимое только на клиенте
3. **withHydrationFix** - HOC для обертывания компонентов
4. **SafeImage** - безопасная работа с изображениями
5. **SafeImageMulti** - улучшенная версия с поддержкой альтернативных источников

### Проблемы с кириллическими именами файлов

```powershell
# Проверка наличия файла с кириллическим именем
dir .\frontend\public\images\Логотип.png

# Проверка всех изображений
dir .\frontend\public\images\
```

### Отладка проблем с гидратацией

```powershell
# Очистка кэша Next.js
cd frontend
npm run clean  # Если команда существует, или
rm -r -fo .next/  # Удаление директории .next вручную

# Перезапуск сервера разработки с очищенным кэшем
npm run dev
```

## Деплой

### Подготовка к production

```powershell
# Запуск production окружения
.\start-prod.sh  # На Linux/Mac
# Или на Windows через WSL:
wsl -e ./start-prod.sh

# Остановка production окружения
.\stop-prod.sh  # На Linux/Mac
# Или на Windows через WSL:
wsl -e ./stop-prod.sh
```

### Проверка статуса контейнеров

```powershell
docker ps  # Просмотр запущенных контейнеров
docker-compose -f docker-compose.prod.yml ps  # Статус контейнеров в production
```

## Документация компонентов

Подробная документация по компонентам находится в README каждого сервиса:

- [Backend документация](./backend/README.md)
- [Frontend документация](./frontend/README.md)
- [Docker документация](./docker/local/README.md)

# Многосайтовая конфигурация с Nginx и Docker

Этот репозиторий содержит конфигурацию для запуска нескольких веб-сайтов (prootzyvy.com и cryptoobmen) на одном сервере с использованием Docker и Nginx.

## Структура проекта

```
docker/
├── docker-compose.yml           # Основной файл для запуска всех сервисов
├── nginx/                       # Настройки Nginx
│   ├── Dockerfile               # Dockerfile для Nginx
│   └── conf.d/                  # Директория с конфигурациями сайтов
│       ├── nginx.conf           # Общие настройки Nginx
│       ├── prootzyvy.conf       # Конфигурация для prootzyvy.com
│       └── cryptoobmen.conf     # Конфигурация для cryptoobmen
├── data/                        # Директория для хранения данных
    ├── django_static/           # Статические файлы Django для prootzyvy
    ├── django_media/            # Медиафайлы Django для prootzyvy
    ├── static/                  # Статические файлы для cryptoobmen
    ├── media/                   # Медиафайлы для cryptoobmen
    └── certbot/                 # SSL сертификаты
```

## Особенности конфигурации

1. **Два изолированных проекта:**
   - prootzyvy.com - доступен по доменному имени prootzyvy.com
   - cryptoobmen - доступен по IP 194.15.46.70

2. **Общий Nginx:**
   - Маршрутизация запросов на основе домена и IP
   - Общие настройки безопасности и производительности

3. **Отдельные базы данных:**
   - Каждый проект использует свою базу данных PostgreSQL

## Запуск проекта

1. Клонируйте репозиторий
   ```bash
   git clone <url-репозитория>
   cd <директория-проекта>
   ```

2. Настройте переменные окружения (отредактируйте docker-compose.yml):
   - Укажите правильные имена образов для ваших проектов
   - Настройте пароли для баз данных
   - Установите другие необходимые переменные окружения

3. Создайте необходимые директории для данных:
   ```bash
   mkdir -p docker/data/{django_static,django_media,static,media,certbot/www,certbot/conf}
   ```

4. Запустите проект:
   ```bash
   cd docker
   docker-compose up -d
   ```

## SSL-сертификаты

Для настройки SSL:
1. Инициализация certbot (для prootzyvy.com):
   ```bash
   docker-compose run --rm certbot certonly --webroot -w /var/www/certbot -d prootzyvy.com -d www.prootzyvy.com
   ```

2. Для cryptoobmen (после получения домена):
   ```bash
   docker-compose run --rm certbot certonly --webroot -w /var/www/certbot -d your-domain.com
   ```

3. После настройки SSL для cryptoobmen, раскомментируйте секцию HTTPS в `docker/nginx/conf.d/cryptoobmen.conf`

## Управление

- Просмотр логов всех контейнеров:
  ```bash
  docker-compose logs -f
  ```

- Перезапуск Nginx:
  ```bash
  docker-compose restart nginx
  ```

- Остановка всех сервисов:
  ```bash
  docker-compose down
  ```

## Обслуживание

- Обновление проектов (пример для prootzyvy):
  ```bash
  docker-compose pull backend-prootzyvy frontend-prootzyvy
  docker-compose up -d --no-deps backend-prootzyvy frontend-prootzyvy
  ```
