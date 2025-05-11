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

# Сборка и запуск контейнеров в продакшен-режиме
log "Сборка и запуск контейнеров..."
docker-compose -f docker-compose.prod.yml build
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

log "Деплой успешно завершен. Приложение доступно по адресу: http://194.15.46.70"
log "Админ-панель: http://194.15.46.70/admin/" 