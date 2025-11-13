from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    # Сначала получаем стандартную обработку исключений DRF
    response = exception_handler(exc, context)

    if response is not None:
        # Добавляем дополнительную информацию в ответ
        error_data = {
            'detail': str(exc),
            'status_code': response.status_code
        }
        
        # Если есть дополнительные детали в исключении
        if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
            error_data.update(exc.detail)
        
        response.data = error_data

    return response 