#!/bin/bash
# Скрипт для остановки продакшен-окружения на Linux

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
    echo -e "${CYAN}  CRYPTOOBMEN - ОСТАНОВКА ПРОДАКШЕНА${NC}"
    echo -e "${CYAN}===========================================${NC}"
    echo ""
}

# Очистка экрана и вывод заголовка
clear_screen_with_header

# Шаг 1: Остановка основных сервисов
echo -e "${YELLOW}Шаг 1: Остановка основных сервисов (бэкенд, фронтенд, nginx)...${NC}"
docker-compose -f docker-compose.prod.yml down
if [ $? -ne 0 ]; then
    echo -e "${RED}Предупреждение: Ошибка при остановке основных сервисов!${NC}"
else
    echo -e "${GREEN}Основные сервисы успешно остановлены!${NC}"
fi

# Шаг 2: Остановка базы данных и Redis
echo -e "\n${YELLOW}Шаг 2: Остановка базы данных PostgreSQL и Redis...${NC}"
cd ./docker/postgres || { echo -e "${RED}Директория postgres не найдена!${NC}"; exit 1; }
docker-compose -f docker-compose.db.yml down
if [ $? -ne 0 ]; then
    echo -e "${RED}Предупреждение: Ошибка при остановке базы данных!${NC}"
    cd ../../
else
    echo -e "${GREEN}База данных и Redis успешно остановлены!${NC}"
    cd ../../
fi

echo -e "\n${GREEN}Все сервисы успешно остановлены!${NC}" 