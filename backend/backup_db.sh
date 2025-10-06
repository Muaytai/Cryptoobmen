#!/bin/bash

# Скрипт для создания бэкапа базы данных
# Использование: ./backup_db.sh [опции]

set -e

# Переходим в директорию проекта
cd "$(dirname "$0")"

# Активируем виртуальное окружение если оно существует
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Запускаем скрипт бэкапа
python3 backup_database.py "$@"
