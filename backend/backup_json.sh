#!/bin/bash

# Скрипт для создания JSON бэкапа базы данных
# Использование: ./backup_json.sh [опции]

set -e

# Переходим в директорию проекта
cd "$(dirname "$0")"

# Активируем виртуальное окружение если оно существует
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Запускаем скрипт JSON бэкапа
python3 backup_json.py "$@"
