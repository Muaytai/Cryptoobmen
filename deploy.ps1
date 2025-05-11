# Скрипт для деплоя проекта на сервер с IP 194.15.46.70 (PowerShell версия)

# Функция для отображения сообщений
function Log {
    param (
        [string]$message
    )
    Write-Host "[+] $message" -ForegroundColor Green
}

function Warn {
    param (
        [string]$message
    )
    Write-Host "[!] $message" -ForegroundColor Yellow
}

function Error {
    param (
        [string]$message
    )
    Write-Host "[-] $message" -ForegroundColor Red
    Exit 1
}

# Проверка наличия файлов окружения
Log "Проверка файлов окружения..."
$ENV_FILES = @(
    "docker/postgres/.env.prod",
    "docker/backend/.env.prod",
    "docker/frontend/.env.prod"
)

foreach ($env_file in $ENV_FILES) {
    if (-not (Test-Path $env_file)) {
        Error "Файл $env_file не найден. Пожалуйста, создайте его на основе example.env.prod"
    }
}

# Сборка и запуск контейнеров в продакшен-режиме
Log "Сборка и запуск контейнеров..."
docker-compose -f docker-compose.prod.yml build
if (-not $?) { Error "Произошла ошибка при сборке контейнеров" }

docker-compose -f docker-compose.prod.yml up -d
if (-not $?) { Error "Произошла ошибка при запуске контейнеров" }

# Выполнение миграций
Log "Применение миграций Django..."
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
if (-not $?) { Warn "Произошла ошибка при выполнении миграций" }

# Создание суперпользователя (опционально)
$answer = Read-Host "Вы хотите создать суперпользователя Django? (y/n)"
if ($answer -eq "y") {
    Log "Создание суперпользователя..."
    docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
}

Log "Деплой успешно завершен. Приложение доступно по адресу: http://194.15.46.70"
Log "Админ-панель: http://194.15.46.70/admin/" 