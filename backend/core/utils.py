import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def verify_recaptcha(token, action=None):
    """
    Проверяет токен reCAPTCHA v3
    
    Args:
        token (str): Токен reCAPTCHA от клиента
        action (str, optional): Ожидаемое действие
        
    Returns:
        tuple: (успех, оценка, ошибка)
    """
    if not token:
        return False, 0.0, "Токен reCAPTCHA не предоставлен"
    
    if not settings.RECAPTCHA_SECRET_KEY:
        logger.warning("RECAPTCHA_SECRET_KEY не настроен")
        return True, 1.0, None  # В режиме разработки пропускаем проверку
    
    try:
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': settings.RECAPTCHA_SECRET_KEY,
                'response': token
            }
        )
        
        result = response.json()
        success = result.get('success', False)
        score = result.get('score', 0.0)
        action_match = True
        
        if action and result.get('action') != action:
            action_match = False
            logger.warning(f"reCAPTCHA действие не совпадает: ожидалось {action}, получено {result.get('action')}")
        
        # Проверяем, что оценка выше порога и действие совпадает
        if success and score >= settings.RECAPTCHA_SCORE_THRESHOLD and action_match:
            return True, score, None
        else:
            error_codes = result.get('error-codes', [])
            error_msg = ', '.join(error_codes) if error_codes else "Недостаточная оценка reCAPTCHA"
            return False, score, error_msg
            
    except Exception as e:
        logger.error(f"Ошибка при проверке reCAPTCHA: {e}")
        return False, 0.0, str(e) 