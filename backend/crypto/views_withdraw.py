from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Cryptocurrency
from .serializers import CryptocurrencySerializer

class WithdrawInfoView(APIView):
    def get(self, request, *args, **kwargs):
        currency_symbol = request.query_params.get('currency')
        network = request.query_params.get('network')

        if not currency_symbol or not network:
            return Response({'error': 'Currency and network are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            crypto = Cryptocurrency.objects.get(symbol=currency_symbol, network=network)
            serializer = CryptocurrencySerializer(crypto)
            # Просто возвращаем информацию о криптовалюте, включая requires_memo
            return Response(serializer.data)
        except Cryptocurrency.DoesNotExist:
            return Response({'error': 'Cryptocurrency not found'}, status=status.HTTP_404_NOT_FOUND)