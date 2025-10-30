#!/bin/bash

# Скрипт для автоматического создания бэкапов с ротацией
# Использование: ./backup_rotation.sh [опции]

set -e

# Переходим в директорию проекта
cd "$(dirname "$0")"

# Активируем виртуальное окружение если оно существует
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Запускаем скрипт ротации бэкапов
python3 backup_rotation.py "$@"
