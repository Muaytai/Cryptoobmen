from django.shortcuts import render
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.db.models import Q, F
from decimal import Decimal
import requests
from datetime import datetime
from django.conf import settings

from .models import Cryptocurrency, CryptoPrice, ExchangePair, UserWallet
from .serializers import (
    CryptocurrencySerializer, CryptoPriceSerializer, ExchangePairSerializer,
    UserWalletSerializer, ExchangeCalculatorSerializer
)


class CryptocurrencyViewSet(viewsets.ModelViewSet):
    """API для работы с криптовалютами"""
    queryset = Cryptocurrency.objects.filter(is_active=True)
    serializer_class = CryptocurrencySerializer
    permission_classes = [AllowAny]
    
    def get_permissions(self):
        """Определяем права доступа в зависимости от действия"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]
    
    @action(detail=False, methods=['get'])
    def get_active(self, request):
        """Возвращает список активных криптовалют"""
        active_cryptocurrencies = Cryptocurrency.objects.filter(is_active=True)
        serializer = self.get_serializer(active_cryptocurrencies, many=True)
        return Response(serializer.data)


class CryptoPriceViewSet(viewsets.ReadOnlyModelViewSet):
    """API для работы с ценами криптовалют"""
    queryset = CryptoPrice.objects.all()
    serializer_class = CryptoPriceSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Получаем последние цены для каждой криптовалюты"""
        queryset = CryptoPrice.objects.none()
        
        # Получаем ID последних цен для каждой криптовалюты
        crypto_ids = Cryptocurrency.objects.filter(is_active=True).values_list('id', flat=True)
        for crypto_id in crypto_ids:
            latest_price = CryptoPrice.objects.filter(crypto_id=crypto_id).order_by('-timestamp').first()
            if latest_price:
                queryset = queryset | CryptoPrice.objects.filter(id=latest_price.id)
                
        return queryset
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Возвращает последние цены для всех криптовалют"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ExchangePairViewSet(viewsets.ModelViewSet):
    """API для работы с парами обмена"""
    queryset = ExchangePair.objects.filter(is_active=True)
    serializer_class = ExchangePairSerializer
    permission_classes = [AllowAny]
    
    def get_permissions(self):
        """Определяем права доступа в зависимости от действия"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]
    
    @action(detail=False, methods=['get'])
    def by_crypto(self, request):
        """Возвращает доступные пары обмена для конкретной криптовалюты"""
        crypto_id = request.query_params.get('crypto_id')
        if not crypto_id:
            return Response({"error": "Необходимо указать crypto_id"}, status=status.HTTP_400_BAD_REQUEST)
        
        from_pairs = ExchangePair.objects.filter(from_crypto_id=crypto_id, is_active=True)
        to_pairs = ExchangePair.objects.filter(to_crypto_id=crypto_id, is_active=True)
        
        from_serializer = self.get_serializer(from_pairs, many=True)
        to_serializer = self.get_serializer(to_pairs, many=True)
        
        return Response({
            "from_pairs": from_serializer.data,
            "to_pairs": to_serializer.data
        })


class UserWalletViewSet(viewsets.ModelViewSet):
    """API для работы с кошельками пользователя"""
    serializer_class = UserWalletSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Пользователь может видеть только свои кошельки"""
        return UserWallet.objects.filter(user=self.request.user, is_active=True)
    
    def get_permissions(self):
        """Определяем права доступа в зависимости от действия"""
        if self.action in ['create', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Возвращает суммарный баланс в долларах"""
        wallets = self.get_queryset()
        total_usd_balance = 0
        
        for wallet in wallets:
            # Получаем последнюю цену для криптовалюты
            latest_price = CryptoPrice.objects.filter(crypto=wallet.crypto).order_by('-timestamp').first()
            if latest_price:
                total_usd_balance += wallet.balance * latest_price.price_usd
        
        return Response({
            "total_usd_balance": round(total_usd_balance, 2)
        })


class ExchangeCalculatorAPIView(generics.GenericAPIView):
    """API для расчета обмена валют"""
    serializer_class = ExchangeCalculatorSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        """Рассчитывает сумму к получению при обмене"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        from_crypto = data['from_crypto']
        to_crypto = data['to_crypto']
        exchange_pair = data['exchange_pair']
        amount = data['amount']
        
        # Получаем последние цены криптовалют
        from_price = CryptoPrice.objects.filter(crypto=from_crypto).order_by('-timestamp').first()
        to_price = CryptoPrice.objects.filter(crypto=to_crypto).order_by('-timestamp').first()
        
        if not from_price or not to_price:
            return Response({"error": "Не удалось получить текущие цены валют"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Рассчитываем курс обмена
        rate = from_price.price_usd / to_price.price_usd
        
        # Рассчитываем комиссию
        fee_percentage = exchange_pair.custom_fee_percentage or from_crypto.fee_percentage
        fee_amount = (amount * fee_percentage) / 100
        
        # Рассчитываем сумму к получению
        to_amount = (amount - fee_amount) * rate
        
        return Response({
            "from_amount": amount,
            "from_crypto": CryptocurrencySerializer(from_crypto).data,
            "to_amount": round(to_amount, 8),
            "to_crypto": CryptocurrencySerializer(to_crypto).data,
            "rate": round(rate, 8),
            "fee_percentage": fee_percentage,
            "fee_amount": round(fee_amount, 8),
            "fee_usd": round(fee_amount * from_price.price_usd, 2)
        })
