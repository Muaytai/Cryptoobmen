#!/bin/bash

# Переходим в директорию скрипта
cd "$(dirname "$0")"

# Останавливаем процессы, которые могут занимать порт 8000
echo "🔍 Проверяем процессы на порту 8000..."
PROCESSES=$(lsof -ti :8000 2>/dev/null)

if [ ! -z "$PROCESSES" ]; then
    echo "⚠️  Найдены процессы на порту 8000: $PROCESSES"
    echo "🛑 Останавливаем их..."
    kill -9 $PROCESSES 2>/dev/null
    sleep 2
    echo "✅ Процессы остановены"
else
    echo "✅ Порт 8000 свободен"
fi

# Активируем виртуальное окружение
echo "🐍 Активируем виртуальное окружение..."
source venv/bin/activate

# Запускаем сервер
echo "🚀 Запускаем Django сервер..."
uvicorn core.asgi:application --host 0.0.0.0 --port 8000 --reload

