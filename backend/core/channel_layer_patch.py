"""
Monkey patch для совместимости channels-redis 4.x с удаленными методами валидации
"""
import re
from channels_redis.core import RedisChannelLayer


def valid_group_name(self, group_name, **kwargs):
    """
    Проверяет валидность имени группы.
    Восстановленный метод для совместимости с channels-redis 4.x
    """
    if not isinstance(group_name, str):
        return False
    
    # Проверяем длину (не более 255 символов для групп)
    if len(group_name) > 255:
        return False
    
    # Проверяем допустимые символы: буквы, цифры, дефис, подчеркивание, точка
    if not re.match(r'^[a-zA-Z0-9\-_.]+$', group_name):
        return False
        
    return True


def valid_channel_name(self, channel_name, **kwargs):
    """
    Проверяет валидность имени канала.
    Восстановленный метод для совместимости с channels-redis 4.x
    """
    if not isinstance(channel_name, str):
        return False
    
    # Проверяем длину (не более 255 символов для каналов)
    if len(channel_name) > 255:
        return False
    
    # Проверяем допустимые символы: буквы, цифры, дефис, подчеркивание, точка, восклицательный знак
    # Channels генерирует имена вида: httpwebsocket.send.mWcGINDy!PEarHGLEjkcP
    if not re.match(r'^[a-zA-Z0-9\-_.!]+$', channel_name):
        return False
        
    return True


# Monkey patch - добавляем отсутствующие методы
RedisChannelLayer.valid_group_name = valid_group_name
RedisChannelLayer.valid_channel_name = valid_channel_name

print("✅ Channel layer patch applied: valid_group_name and valid_channel_name methods restored")
