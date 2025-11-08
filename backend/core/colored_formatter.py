"""
Цветной форматтер для логов Django/Celery
"""
import logging
import sys
import os


class ColoredFormatter(logging.Formatter):
    """
    Цветной форматтер для логов с поддержкой ANSI escape кодов
    """
    
    # Цветовые коды
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    
    # Сброс цвета
    RESET = '\033[0m'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Проверяем, поддерживает ли терминал цвета
        self.supports_color = self._supports_color()
    
    def _supports_color(self):
        """
        Проверяет, поддерживает ли терминал цветной вывод
        """
        # Проверяем переменные окружения
        if 'NO_COLOR' in os.environ:
            return False
        
        # Проверяем, что это не файл
        if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
            return False
        
        # Проверяем платформу
        if os.name == 'nt':  # Windows
            return True
        
        # Проверяем TERM переменную
        term = os.environ.get('TERM', '').lower()
        return term in ('xterm', 'xterm-color', 'xterm-256color', 'screen', 'screen-256color', 'tmux', 'tmux-256color')
    
    def format(self, record):
        """
        Форматирует лог запись с цветами
        """
        # Получаем базовое форматирование
        formatted = super().format(record)
        
        # Если цвета не поддерживаются, возвращаем без изменений
        if not self.supports_color:
            return formatted
        
        # Применяем цвет к уровню логирования
        level_name = record.levelname
        if level_name in self.COLORS:
            # Находим уровень в строке и заменяем его на цветной
            color = self.COLORS[level_name]
            formatted = formatted.replace(level_name, f"{color}{level_name}{self.RESET}")
        
        # Обрабатываем специальные цветные сообщения в самом сообщении
        # Это для наших кастомных цветных логов из tasks_consolidation.py
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            # Уже обработанные цветные сообщения оставляем как есть
            if '\033[' in record.msg:
                return formatted
        
        return formatted
