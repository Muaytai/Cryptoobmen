from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .services_deposit import DepositService
from .serializers import DepositInfoRequestSerializer
from .models import UserDepositMemo
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
import logging

logger = logging.getLogger(__name__)


class DepositInfoView(APIView):
    """
    API для получения информации для пополнения кошелька.
    Возвращает системный адрес и уникальный Memo для пользователя.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Принимает:
        - currency_symbol: 'USDT'
        - network: 'TRC20'
        """
        serializer = DepositInfoRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        currency_symbol = validated_data['currency_symbol']
        network = validated_data['network']
        user = request.user

        try:
            address, memo = DepositService.get_deposit_info(
                user=user,
                currency_symbol=currency_symbol,
                network=network
            )

            if not address:
                return Response(
                    {'error': f'Депозиты для {currency_symbol} в сети {network} временно недоступны.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response({
                'address': address,
                'memo': memo,
                'currency': currency_symbol,
                'network': network
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            # Ошибки валидации бизнес-логики (не найдено или недоступно)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("deposit/info failed: %s", e)
            return Response(
                {'error': 'Произошла внутренняя ошибка. Попробуйте позже.'},
                status=status.HTTP_400_BAD_REQUEST
            )


@method_decorator(never_cache, name='get')
class DepositStatusView(APIView):
    """
    Проверяет статус конкретного Memo на пополнение.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, memo, *args, **kwargs):
        try:
            deposit_memo = UserDepositMemo.objects.get(memo=memo, user=request.user)
            return Response({"status": deposit_memo.status})
        except UserDepositMemo.DoesNotExist:
            return Response({"error": "Memo not found or does not belong to user."}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500) 