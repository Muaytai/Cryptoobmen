"""
Система блокировок для предотвращения параллельного выполнения критических задач Celery
"""
import time
import logging
from functools import wraps
from django.core.cache import cache

logger = logging.getLogger(__name__)

def single_instance_task(timeout=300):
    """
    Декоратор для предотвращения параллельного выполнения задачи.
    
    Args:
        timeout: Время жизни блокировки в секундах (по умолчанию 5 минут)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Создаем уникальный ключ блокировки на основе имени функции
            lock_key = f"task_lock_{func.__name__}"
            
            # Пытаемся получить блокировку
            existing_lock = cache.get(lock_key)
            if existing_lock:
                message = f"Task {func.__name__} already running, skipping execution"
                logger.warning(message)
                print(f"⚠️ {message}")  # Для отладки
                return message
            
            # Устанавливаем блокировку
            cache.set(lock_key, time.time(), timeout)
            lock_message = f"Acquired lock for task {func.__name__}"
            logger.info(lock_message)
            print(f"🔒 {lock_message}")  # Для отладки
            
            try:
                # Выполняем задачу
                result = func(*args, **kwargs)
                return result
            finally:
                # Освобождаем блокировку
                cache.delete(lock_key)
                release_message = f"Released lock for task {func.__name__}"
                logger.info(release_message)
                print(f"🔓 {release_message}")  # Для отладки
        
        return wrapper
    return decorator
