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
