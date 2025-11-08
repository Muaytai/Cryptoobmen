#!/bin/bash
# Полный запуск Celery системы (Workers + Beat) для Linux

# Сохраняем текущую директорию
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📂 Рабочая директория: $SCRIPT_DIR"
echo "🚀 Запуск полной Celery системы..."
echo ""

# Останавливаем все старые процессы
echo "🛑 Остановка старых процессов..."
pkill -f "celery.*worker" 2>/dev/null
pkill -f "celery.*beat" 2>/dev/null
echo "   Процессы остановлены"
sleep 3
echo "   Ожидание завершено"

echo ""
echo "🔧 Создаем директорию для логов..."
mkdir -p "$SCRIPT_DIR/logs/celery"

echo ""
echo "🔧 Запуск Workers..."

# Проверяем и активируем виртуальное окружение
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
    echo "   ✅ Виртуальное окружение активировано"
else
    echo "   ⚠️  Виртуальное окружение не найдено, используем системный Python"
fi

# Запускаем workers в фоне с логированием
echo "   🚀 Запуск High priority worker..."
celery -A core worker -l info -Q high_priority -n high_priority_worker --concurrency=2 \
    --logfile="$SCRIPT_DIR/logs/celery/high_priority.log" &
HIGH_PID=$!
echo "   ⚡ High priority worker: PID $HIGH_PID"

echo "   🚀 Запуск Medium priority worker..."
celery -A core worker -l info -Q medium_priority -n medium_priority_worker --concurrency=2 \
    --logfile="$SCRIPT_DIR/logs/celery/medium_priority.log" &
MEDIUM_PID=$!
echo "   🔄 Medium priority worker: PID $MEDIUM_PID"

echo "   🚀 Запуск Low priority worker..."
celery -A core worker -l info -Q low_priority -n low_priority_worker --concurrency=2 \
    --logfile="$SCRIPT_DIR/logs/celery/low_priority.log" &
LOW_PID=$!
echo "   📊 Low priority worker: PID $LOW_PID"

sleep 3

echo ""
echo "⏰ Запуск Beat scheduler..."
celery -A core beat --loglevel=info --logfile="$SCRIPT_DIR/logs/celery/beat.log" &
BEAT_PID=$!
echo "   🕒 Beat scheduler: PID $BEAT_PID"

sleep 3

echo ""
echo "✅ Система запущена!"
echo ""
echo "📊 Статус процессов:"
WORKER_COUNT=$(ps aux | grep -E "celery.*worker" | grep -v grep | wc -l)
BEAT_COUNT=$(ps aux | grep -E "celery.*beat" | grep -v grep | wc -l)
echo "   Workers: $WORKER_COUNT процессов"
echo "   Beat: $BEAT_COUNT процесс"

echo ""
echo "📁 Файлы логов:"
echo "   High priority: $SCRIPT_DIR/logs/celery/high_priority.log"
echo "   Medium priority: $SCRIPT_DIR/logs/celery/medium_priority.log"
echo "   Low priority: $SCRIPT_DIR/logs/celery/low_priority.log"
echo "   Beat: $SCRIPT_DIR/logs/celery/beat.log"

echo ""
echo "🔧 Управление:"
echo "   Остановка: $SCRIPT_DIR/stop_celery_system_linux.sh"
echo "   Просмотр логов: tail -f $SCRIPT_DIR/logs/celery/*.log"
echo "   Статус: ps aux | grep celery"
echo "   Мониторинг: celery -A core inspect active"

echo ""
echo "🟢 Система готова к работе!"
echo ""
echo "📊 Вывод логов всех процессов (Ctrl+C для остановки просмотра):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Обработчик сигналов для корректной остановки
trap 'echo ""; echo ""; echo "🛑 Для остановки системы используйте: $SCRIPT_DIR/stop_celery_system_linux.sh"; exit 0' SIGINT SIGTERM

# Показываем логи всех процессов в реальном времени
tail -f "$SCRIPT_DIR/logs/celery/"*.log

