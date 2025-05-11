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

# Запрос пользователя о режиме запуска
Warn "Выберите режим запуска:"
Write-Host "1. Только база данных и Redis (рекомендуется для начала)"
Write-Host "2. Полный стек (база данных, backend, frontend, nginx)"
Write-Host "3. Только приложение (если база данных уже запущена)"
$deploy_mode = Read-Host "Введите номер (1-3)"

switch ($deploy_mode) {
    "1" {
        Log "Запуск только базы данных и Redis..."
        Set-Location -Path docker/postgres
        docker-compose -f docker-compose.db.yml up -d
        if (-not $?) { Error "Произошла ошибка при запуске базы данных" }
        Set-Location -Path ../..
        Log "База данных и Redis успешно запущены!"
    }
    "2" {
        Log "Запуск полного стека..."
        # Сначала запускаем базу данных
        Set-Location -Path docker/postgres
        docker-compose -f docker-compose.db.yml up -d
        if (-not $?) { Error "Произошла ошибка при запуске базы данных" }
        Set-Location -Path ../..
        
        # Затем запускаем основные сервисы
        Log "Запуск основных сервисов..."
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
    }
    "3" {
        Log "Запуск только приложения (без базы данных)..."
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
    }
    default {
        Error "Неверный выбор. Пожалуйста, введите число от 1 до 3."
    }
}

Log "Деплой успешно завершен. Приложение доступно по адресу: http://194.15.46.70"
Log "Админ-панель: http://194.15.46.70/admin/" 