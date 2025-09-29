# Проверка запуска задач консолидации через Celery Beat

## Краткий ответ

**ДА**, задачи консолидации должны запускаться по команде `celery -A core beat -l info`.

## Настроенные задачи в CELERY_BEAT_SCHEDULE

В `core/settings.py` настроены следующие задачи консолидации:

```python
CELERY_BEAT_SCHEDULE = {
    'consolidate-user-deposits-every-5-minutes': {
        'task': 'crypto.tasks_consolidation.consolidate_user_deposits',
        'schedule': 300.0,  # 5 минут
    },
    'check-consolidation-confirmations-every-minute': {
        'task': 'crypto.tasks_consolidation.check_consolidation_confirmations', 
        'schedule': 60.0,   # 1 минута
    },
}
```

## Команды для проверки

### 1. Проверка регистрации задач
```bash
python manage.py check_celery_tasks
```

### 2. Проверка настроек расписания
```bash
python manage.py test_consolidation_tasks --check-schedule
```

### 3. Тестирование задач напрямую
```bash
# Тест консолидации
python manage.py test_consolidation_tasks --test-consolidation

# Тест проверки подтверждений
python manage.py test_consolidation_tasks --test-check-confirmations
```

## Запуск Celery Beat

### Команда для запуска:
```bash
celery -A core beat -l info
```

### Ожидаемый вывод:
```
[2025-01-XX XX:XX:XX,XXX: INFO/MainProcess] beat: Starting...
[2025-01-XX XX:XX:XX,XXX: INFO/MainProcess] Scheduler: Sending due task consolidate-user-deposits-every-5-minutes
[2025-01-XX XX:XX:XX,XXX: INFO/MainProcess] Scheduler: Sending due task check-consolidation-confirmations-every-minute
```

## Запуск Celery Worker

Для выполнения задач нужен активный worker:

```bash
# Основной worker
celery -A core worker -l info

# Worker для средней важности (консолидация)
celery -A core worker -l info -Q medium_priority
```

## Очереди задач

Задачи консолидации настроены на очередь **medium_priority**:

```python
CELERY_TASK_ROUTES = {
    'crypto.tasks_consolidation.consolidate_user_deposits': {'queue': 'medium_priority'},
    'crypto.tasks_consolidation.check_consolidation_confirmations': {'queue': 'medium_priority'},
}
```

## Возможные проблемы и решения

### 1. Задачи не найдены
**Симптом**: `KeyError: 'crypto.tasks_consolidation.consolidate_user_deposits'`

**Решение**:
```bash
# Проверить импорты
python -c "from crypto.tasks_consolidation import consolidate_user_deposits; print('OK')"

# Перезапустить Celery
```

### 2. Модуль не найден
**Симптом**: `ModuleNotFoundError: No module named 'crypto.tasks_consolidation'`

**Решение**: Проверить файл `crypto/__init__.py` содержит импорт:
```python
from . import tasks_consolidation
```

### 3. Beat не видит расписание
**Симптом**: Задачи не запускаются по расписанию

**Решение**: Проверить `CELERY_BEAT_SCHEDULE` в settings.py и перезапустить beat

## Мониторинг

### Проверка активных задач:
```bash
celery -A core inspect active
```

### Проверка расписания:
```bash
celery -A core beat --loglevel=debug
```

### Просмотр логов консолидации:
```bash
tail -f logs/django.log | grep consolidation
```

## Итог

При правильной настройке команда `celery -A core beat -l info` **автоматически запустит** задачи консолидации:

- **consolidate_user_deposits** - каждые 5 минут
- **check_consolidation_confirmations** - каждую минуту

Задачи будут отправляться в очередь `medium_priority` и выполняться соответствующим worker'ом.