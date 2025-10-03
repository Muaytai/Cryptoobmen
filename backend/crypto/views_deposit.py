from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .services_deposit import DepositService
import logging

logger = logging.getLogger(__name__)

class DepositInfoView(APIView):
    """
    View для получения информации для депозита (адрес и memo, если требуется).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Возвращает адрес и memo для пополнения указанной валюты.
        Принимает query-параметры: `currency` и `network`.
        """
        currency_symbol = request.query_params.get('currency') or request.query_params.get('currency_symbol')
        network = request.query_params.get('network')

        # Добавляем логирование для отладки
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"DepositInfoView: currency={currency_symbol}, network={network}")

        if not currency_symbol or not network:
            return Response(
                {"error": "Параметры 'currency' и 'network' обязательны."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = DepositService.get_deposit_info(
                user=request.user,
                currency_symbol=currency_symbol,
                network=network
            )
            
            # Обрабатываем результат в зависимости от количества возвращаемых значений
            if len(result) == 4:
                address, memo, qr_code, gas_info = result
            else:
                # Обратная совместимость со старым форматом
                address, memo, qr_code = result
                gas_info = None
            
            response_data = {
                'address': address,
                'memo': memo,
                'currency_symbol': currency_symbol,
                'network': network,
                'qr_code': qr_code
            }
            
            # Добавляем информацию о газе для валют без мемо
            if gas_info is not None:
                response_data['gas_info'] = gas_info
            
            return Response(response_data, status=status.HTTP_200_OK)

        except ValueError as e:
            logger.warning(f"Error getting deposit info for user {request.user.id}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in DepositInfoView for user {request.user.id}: {e}", exc_info=True)
            return Response({"error": "Произошла внутренняя ошибка сервера."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
