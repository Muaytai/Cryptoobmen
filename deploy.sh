#!/bin/bash

# Скрипт для деплоя проекта на сервер с IP 194.15.46.70

# Выход из скрипта при ошибках
set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Функция для отображения сообщений
function log {
    echo -e "${GREEN}[+] $1${NC}"
}

function warn {
    echo -e "${YELLOW}[!] $1${NC}"
}

function error {
    echo -e "${RED}[-] $1${NC}"
    exit 1
}

# Проверка наличия файлов окружения
log "Проверка файлов окружения..."
ENV_FILES=(
    "docker/postgres/.env.prod"
    "docker/backend/.env.prod"
    "docker/frontend/.env.prod"
)

for env_file in "${ENV_FILES[@]}"; do
    if [ ! -f "$env_file" ]; then
        error "Файл $env_file не найден. Пожалуйста, создайте его на основе example.env.prod"
    fi
done

# Запрос пользователя о режиме запуска
warn "Выберите режим запуска:"
echo "1. Только база данных и Redis (рекомендуется для начала)"
echo "2. Полный стек (база данных, backend, frontend, nginx)"
echo "3. Только приложение (если база данных уже запущена)"
read -p "Введите номер (1-3): " deploy_mode

case $deploy_mode in
    1)
        log "Запуск только базы данных и Redis..."
        cd docker/postgres
        docker-compose -f docker-compose.db.yml up -d
        cd ../..
        log "База данных и Redis успешно запущены!"
        ;;
    2)
        log "Запуск полного стека..."
        # Сначала запускаем базу данных
        cd docker/postgres
        docker-compose -f docker-compose.db.yml up -d
        cd ../..
        
        # Затем запускаем основные сервисы
        log "Запуск основных сервисов..."
        docker-compose -f docker-compose.prod.yml up -d
        
        # Выполнение миграций
        log "Применение миграций Django..."
        docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
        
        # Создание суперпользователя (опционально)
        warn "Вы хотите создать суперпользователя Django? (y/n)"
        read answer
        if [ "$answer" = "y" ]; then
            log "Создание суперпользователя..."
            docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
        fi
        ;;
    3)
        log "Запуск только приложения (без базы данных)..."
        docker-compose -f docker-compose.prod.yml up -d
        
        # Выполнение миграций
        log "Применение миграций Django..."
        docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
        
        # Создание суперпользователя (опционально)
        warn "Вы хотите создать суперпользователя Django? (y/n)"
        read answer
        if [ "$answer" = "y" ]; then
            log "Создание суперпользователя..."
            docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
        fi
        ;;
    *)
        error "Неверный выбор. Пожалуйста, введите число от 1 до 3."
        ;;
esac

log "Деплой успешно завершен. Приложение доступно по адресу: http://194.15.46.70"
log "Админ-панель: http://194.15.46.70/admin/" 