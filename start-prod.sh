#!/bin/bash
# Скрипт для запуска продакшен-окружения на Linux

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Функция для очистки экрана
clear_screen_with_header() {
    clear
    echo -e "${CYAN}===========================================${NC}"
    echo -e "${CYAN}  CRYPTOOBMEN - ПРОДАКШЕН ОКРУЖЕНИЕ${NC}"
    echo -e "${CYAN}===========================================${NC}"
    echo ""
}

# Очистка экрана и вывод заголовка
clear_screen_with_header

# Проверка наличия Docker
echo -e "${YELLOW}Проверка наличия Docker...${NC}"
if ! [ -x "$(command -v docker)" ]; then
    echo -e "${RED}Docker не найден! Пожалуйста, установите Docker.${NC}"
    exit 1
fi
DOCKER_VERSION=$(docker --version)
echo -e "${GREEN}Docker найден: $DOCKER_VERSION${NC}"

# Проверка наличия Docker Compose
echo -e "${YELLOW}Проверка наличия Docker Compose...${NC}"
if ! [ -x "$(command -v docker-compose)" ]; then
    echo -e "${RED}Docker Compose не найден! Пожалуйста, установите Docker Compose.${NC}"
    exit 1
fi
COMPOSE_VERSION=$(docker-compose --version)
echo -e "${GREEN}Docker Compose найден: $COMPOSE_VERSION${NC}"

# Шаг 1: Запуск базы данных и Redis
echo -e "\n${YELLOW}Шаг 1: Запуск базы данных PostgreSQL и Redis...${NC}"
echo "Запускаем docker-compose для базы данных и Redis..."

cd ./docker/postgres || { echo -e "${RED}Директория postgres не найдена!${NC}"; exit 1; }
docker-compose -f docker-compose.db.yml up -d
if [ $? -ne 0 ]; then
    echo -e "${RED}Ошибка при запуске базы данных!${NC}"
    cd ../../
    exit 1
fi
cd ../../

echo -e "${GREEN}База данных и Redis успешно запущены!${NC}"

# Шаг 2: Запуск основных контейнеров
echo -e "\n${YELLOW}Шаг 2: Запуск основных сервисов (бэкенд, фронтенд, nginx)...${NC}"
echo "Запускаем docker-compose для основных сервисов..."

docker-compose -f docker-compose.prod.yml up -d
if [ $? -ne 0 ]; then
    echo -e "${RED}Ошибка при запуске основных сервисов!${NC}"
    exit 1
fi

echo -e "\n${GREEN}Все сервисы успешно запущены!${NC}"
echo -e "${CYAN}Проект доступен по адресу: http://194.15.46.70${NC}"
echo -e "${CYAN}Панель администратора: http://194.15.46.70/admin/${NC}"
echo ""
echo -e "${YELLOW}Для остановки всех контейнеров выполните:${NC}"
echo "docker-compose -f docker-compose.prod.yml down"
echo "docker-compose -f ./docker/postgres/docker-compose.db.yml down" 