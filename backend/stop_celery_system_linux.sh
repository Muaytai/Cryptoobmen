#!/bin/bash
# Остановка Celery системы для Linux

echo "🛑 Остановка Celery системы..."
echo ""

# Показываем текущие процессы
echo "📊 Текущие процессы:"
ps aux | grep -E "celery.*(worker|beat)" | grep -v grep

echo ""
echo "⏳ Останавливаем процессы..."

# Останавливаем все процессы Celery
pkill -f "celery.*worker" 2>/dev/null
pkill -f "celery.*beat" 2>/dev/null

sleep 3

# Проверяем, остались ли процессы
REMAINING=$(ps aux | grep -E "celery.*(worker|beat)" | grep -v grep | wc -l)

if [ $REMAINING -gt 0 ]; then
    echo "⚠️  Некоторые процессы не остановились, принудительная остановка..."
    pkill -9 -f "celery.*worker" 2>/dev/null
    pkill -9 -f "celery.*beat" 2>/dev/null
    sleep 2
fi

# Финальная проверка
FINAL_COUNT=$(ps aux | grep -E "celery.*(worker|beat)" | grep -v grep | wc -l)

if [ $FINAL_COUNT -eq 0 ]; then
    echo "✅ Все процессы Celery остановлены"
else
    echo "⚠️  Внимание: остались процессы ($FINAL_COUNT)"
    ps aux | grep -E "celery.*(worker|beat)" | grep -v grep
fi

echo ""
echo "📁 Логи сохранены в: logs/celery/"
echo "🔍 Просмотр последних логов: tail logs/celery/*.log"

