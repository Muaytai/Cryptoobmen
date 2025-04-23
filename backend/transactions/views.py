from django.shortcuts import render
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q
from django.utils import timezone

from .models import Transaction, Exchange, Deposit, Withdrawal
from .serializers import (
    TransactionSerializer, ExchangeSerializer, DepositSerializer,
    WithdrawalSerializer, ExchangeCreateSerializer, WithdrawalCreateSerializer
)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """API для просмотра транзакций пользователя"""
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Пользователь может видеть только свои транзакции"""
        user = self.request.user
        return Transaction.objects.filter(user=user).order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Фильтрует транзакции по типу"""
        transaction_type = request.query_params.get('type')
        if not transaction_type:
            return Response({"error": "Необходимо указать тип транзакции"}, status=status.HTTP_400_BAD_REQUEST)
        
        transactions = self.get_queryset().filter(type=transaction_type)
        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Возвращает последние 10 транзакций"""
        transactions = self.get_queryset()[:10]
        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)


class ExchangeViewSet(viewsets.ModelViewSet):
    """API для обмена криптовалют"""
    serializer_class = ExchangeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Пользователь может видеть только свои обмены"""
        user = self.request.user
        return Exchange.objects.filter(user=user).order_by('-timestamp')
    
    def get_serializer_class(self):
        """Выбираем сериализатор в зависимости от действия"""
        if self.action == 'create':
            return ExchangeCreateSerializer
        return ExchangeSerializer
    
    def create(self, request, *args, **kwargs):
        """Создает новый обмен криптовалют"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        exchange = serializer.save()
        
        # Возвращаем созданный обмен через основной сериализатор
        response_serializer = ExchangeSerializer(exchange)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class WithdrawalViewSet(viewsets.ModelViewSet):
    """API для вывода криптовалют"""
    serializer_class = WithdrawalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Пользователь может видеть только свои выводы"""
        user = self.request.user
        return Withdrawal.objects.filter(user=user).order_by('-transaction__timestamp')
    
    def get_serializer_class(self):
        """Выбираем сериализатор в зависимости от действия"""
        if self.action == 'create':
            return WithdrawalCreateSerializer
        return WithdrawalSerializer
    
    def create(self, request, *args, **kwargs):
        """Создает новый запрос на вывод средств"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        withdrawal = serializer.save()
        
        # Возвращаем созданный вывод через основной сериализатор
        response_serializer = WithdrawalSerializer(withdrawal)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Отменяет запрос на вывод"""
        withdrawal = self.get_object()
        
        # Проверяем, можно ли отменить
        if withdrawal.transaction.status != 'pending':
            return Response({"error": "Можно отменить только ожидающие подтверждения выводы"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Отменяем вывод и возвращаем средства
        withdrawal.transaction.status = 'cancelled'
        withdrawal.transaction.save()
        
        # Возвращаем средства
        wallet = withdrawal.wallet
        wallet.balance += withdrawal.transaction.amount
        wallet.save()
        
        serializer = self.get_serializer(withdrawal)
        return Response(serializer.data)


class DepositViewSet(viewsets.ReadOnlyModelViewSet):
    """API для просмотра депозитов"""
    serializer_class = DepositSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Пользователь может видеть только свои депозиты"""
        user = self.request.user
        return Deposit.objects.filter(user=user).order_by('-transaction__timestamp')
