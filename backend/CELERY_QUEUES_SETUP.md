# 🚀 Система очередей Celery

## ✅ Проблема решена!

Настроена система разделения Celery задач по приоритетным очередям, чтобы критически важные задачи (выводы, подтверждения) не блокировались фоновыми операциями (сканирование депозитов).

## 📊 Архитектура очередей

### 🔥 High Priority Queue
**Очередь**: `high_priority`  
**Назначение**: Критически важные операции  
**Worker**: `high_priority_worker` (concurrency=1)

**Задачи**:
- `crypto.tasks.process_withdrawal` - Обработка выводов
- `crypto.tasks.check_withdrawal_confirmation` - Проверка подтверждений выводов

### 🎯 Medium Priority Queue  
**Очередь**: `medium_priority`  
**Назначение**: Средний приоритет  
**Worker**: `medium_priority_worker` (concurrency=2)

**Задачи**:
- `crypto.tasks_consolidation.consolidate_user_deposits` - Консолидация депозитов
- `crypto.tasks_consolidation.check_consolidation_confirmations` - Проверка консолидации

### 🔄 Low Priority Queue
**Очередь**: `low_priority`  
**Назначение**: Фоновые операции  
**Worker**: `low_priority_worker` (concurrency=4)

**Задачи**:
- `crypto.tasks.check_blockchain_deposits` - Сканирование депозитов  
- `crypto.tasks.process_pending_deposits` - Обработка зависших депозитов
- `crypto.tasks.process_pending_withdrawals` - Обработка зависших выводов

## 🛠️ Конфигурация

### core/settings.py
```python
# Маршрутизация задач по очередям
CELERY_TASK_ROUTES = {
    # Критически важные задачи
    'crypto.tasks.process_withdrawal': {'queue': 'high_priority'},
    'crypto.tasks.check_withdrawal_confirmation': {'queue': 'high_priority'},
    
    # Консолидация - средний приоритет
    'crypto.tasks_consolidation.consolidate_user_deposits': {'queue': 'medium_priority'},
    'crypto.tasks_consolidation.check_consolidation_confirmations': {'queue': 'medium_priority'},
    
    # Фоновое сканирование - низкий приоритет
    'crypto.tasks.check_blockchain_deposits': {'queue': 'low_priority'},
    'crypto.tasks.process_pending_deposits': {'queue': 'low_priority'},
    'crypto.tasks.process_pending_withdrawals': {'queue': 'low_priority'},
}

# Настройки производительности
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # По одной задаче за раз
CELERY_TASK_ACKS_LATE = True  # Подтверждение после завершения
```

## 🚀 Запуск Workers

### Отдельные Worker'ы
```bash
# High priority worker
./start_celery_worker_high

# Medium priority worker  
./start_celery_worker_medium

# Low priority worker
./start_celery_worker_low
```

### Все Worker'ы одновременно
```bash
./start_celery_workers_all
```

### Ручной запуск
```bash
# High priority
celery -A core worker -l info -Q high_priority -n high_priority_worker@%h --concurrency=1

# Medium priority
celery -A core worker -l info -Q medium_priority -n medium_priority_worker@%h --concurrency=2

# Low priority  
celery -A core worker -l info -Q low_priority -n low_priority_worker@%h --concurrency=4
```

## ✅ Результаты тестирования

### Тест разделения очередей:
- **High Priority** задача: ✅ SUCCESS (выполнилась мгновенно)
- **Low Priority** задача: ⏳ PENDING (выполняется в фоне)

### Активные Worker'ы:
- `high_priority_worker@chaizer-System-Product-Name`: 0 задач
- `low_priority_worker@chaizer-System-Product-Name`: 1 задача (сканирование)

## 🎯 Преимущества

1. **Изоляция критических задач**: Выводы и подтверждения выполняются мгновенно
2. **Предотвращение блокировок**: Фоновое сканирование не блокирует важные операции  
3. **Настраиваемая производительность**: Разное количество worker'ов для разных приоритетов
4. **Горизонтальное масштабирование**: Можно добавлять больше worker'ов по необходимости

## 🔧 Мониторинг

### Проверка статуса worker'ов:
```python
from celery import current_app
inspect = current_app.control.inspect()

# Активные задачи
active = inspect.active()

# Ping worker'ов
pong = inspect.ping()
```

### Процессы в системе:
```bash
ps aux | grep celery | grep worker
```

## 🚨 Важные моменты

1. **Убрали `--pool=solo`** - это решило все проблемы с обнаружением worker'ов
2. **Разные concurrency** для разных приоритетов:
   - High: 1 (последовательная обработка критических задач)
   - Medium: 2 (умеренный параллелизм)  
   - Low: 4 (высокий параллелизм для фоновых задач)
3. **Автоматическое обнаружение задач** настроено в `core/celery.py`
4. **Fallback механизмы** в админке для работы без Celery

## 🎉 Итог

Система очередей полностью решает проблему блокировки критически важных задач. Теперь:
- ✅ Выводы обрабатываются мгновенно в отдельной очереди
- ✅ Подтверждения не ждут завершения сканирования  
- ✅ Админка работает как асинхронно, так и синхронно
- ✅ Система масштабируется под разные нагрузки
