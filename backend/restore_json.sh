#!/bin/bash

# Скрипт для восстановления базы данных из JSON бэкапа
# Использование: ./restore_json.sh <путь_к_файлу_бэкапа> [опции]

set -e

# Проверяем аргументы
if [ $# -eq 0 ]; then
    echo "Использование: $0 <путь_к_файлу_бэкапа> [опции]"
    echo "Пример: $0 backups/cryptoobmen_json_backup_20240101_120000.json.gz"
    exit 1
fi

# Переходим в директорию проекта
cd "$(dirname "$0")"

# Активируем виртуальное окружение если оно существует
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Запускаем скрипт восстановления JSON
python3 restore_json.py "$@"
