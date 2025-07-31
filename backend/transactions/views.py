from django.shortcuts import render
from rest_framework import viewsets, status, generics, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, NumberFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view, permission_classes as dec_permission_classes
from rest_framework import serializers
from .services import WithdrawalService
import uuid

from crypto.models import Cryptocurrency, UserWallet
from .models import Transaction, Exchange, Deposit, Withdrawal, Review
from .serializers import (
    TransactionSerializer, ExchangeSerializer, DepositSerializer,
    WithdrawalSerializer, ExchangeCreateSerializer, WithdrawalCreateSerializer,
    ReviewSerializer, TransactionHistorySerializer
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
        return Response({"message": "Запрос на вывод создан. Пожалуйста, проверьте свою электронную почту, чтобы подтвердить операцию."}, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Отменяет запрос на вывод"""
        withdrawal = self.get_object()
        
        # Проверяем, можно ли отменить
        if withdrawal.transaction.status not in ['pending', 'processing']:
            return Response({"error": "Можно отменить только ожидающие или обрабатываемые выводы"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Отменяем вывод
        withdrawal.status = 'cancelled'
        
        serializer = self.get_serializer(withdrawal)
        return Response(serializer.data)
        
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Изменяет статус вывода (только для администраторов)"""
        if not request.user.is_staff:
            return Response({"error": "Только администраторы могут изменять статус вывода"}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        withdrawal = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response({"error": "Необходимо указать новый статус"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        valid_statuses = [status[0] for status in Transaction.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response({"error": f"Недопустимый статус. Доступные статусы: {valid_statuses}"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Изменяем статус
        withdrawal.status = new_status
        
        serializer = self.get_serializer(withdrawal)
        return Response(serializer.data)


@api_view(['GET'])
@dec_permission_classes([AllowAny])
def confirm_withdrawal_view(request, token):
    """
    View для подтверждения вывода по токену из email.
    """
    try:
        token_uuid = uuid.UUID(token, version=4)
        WithdrawalService.confirm_withdrawal(token_uuid)
        # TODO: Сделать красивую HTML страницу для ответа
        return Response({"message": "Вывод средств успешно подтвержден и поставлен в очередь на обработку."}, status=status.HTTP_200_OK)
    except (ValueError, serializers.ValidationError) as e:
        # TODO: Сделать красивую HTML страницу для ошибки
        error_message = str(e.detail[0]) if isinstance(e, serializers.ValidationError) else "Неверный формат токена."
        return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)


class DepositViewSet(viewsets.ViewSet):
    """API для депозитов"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Пользователь может видеть только свои депозиты"""
        user = self.request.user
        return Deposit.objects.filter(user=user).order_by('-transaction__timestamp')

    def list(self, request):
        """Возвращает список депозитов пользователя"""
        queryset = self.get_queryset()
        serializer = DepositSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='address')
    def get_deposit_address(self, request):
        """
        Возвращает или создает адрес для пополнения.
        """
        user = request.user
        currency_id = request.data.get('currency_id')

        if not currency_id:
            return Response({"error": "currency_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            currency = Cryptocurrency.objects.get(id=currency_id)
            wallet, created = UserWallet.objects.get_or_create(user=user, currency=currency)

            if not wallet.deposit_address:
                # Предполагаем, что у нас есть сервис для создания адресов
                from crypto.blockchain.tron import TronService
                service = TronService()
                address, private_key = service.create_new_address()
                wallet.deposit_address = address
                # Важно: шифрование ключа перед сохранением
                wallet.encrypted_private_key = wallet.encrypt_private_key(private_key)
                wallet.save()

            return Response({'address': wallet.deposit_address}, status=status.HTTP_200_OK)

        except Cryptocurrency.DoesNotExist:
            return Response({"error": "Invalid currency_id"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReviewFilter(FilterSet):
    """Фильтры для отзывов"""
    min_rating = NumberFilter(field_name='rating', lookup_expr='gte')
    max_rating = NumberFilter(field_name='rating', lookup_expr='lte')
    
    class Meta:
        model = Review
        fields = {
            'rating': ['exact'],
            'is_verified': ['exact'],
            'is_published': ['exact'],
            'created_at': ['gte', 'lte'],
        }


class ReviewPagination(PageNumberPagination):
    """Пагинация для отзывов"""
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100


class ReviewViewSet(viewsets.ModelViewSet):
    """API для работы с отзывами"""
    queryset = Review.objects.filter(is_published=True)
    serializer_class = ReviewSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = ReviewFilter
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    search_fields = ['name', 'content']
    pagination_class = ReviewPagination
    
    def get_permissions(self):
        """
        Получение отзывов - для всех.
        Создание - для авторизованных или анонимных.
        Изменение/удаление - только для администраторов.
        """
        if self.action == 'create':
            permission_classes = []
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        """Создание нового отзыва"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        review = serializer.save(
            is_verified=False,
            is_published=False,  # Требуется модерация
        )
        
        # Если пользователь авторизован, привязываем отзыв к нему
        if request.user.is_authenticated:
            review.user = request.user
            review.save()
        
        # Сохраняем IP-адрес пользователя
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        review.ip_address = ip
        review.save()
        
        return Response(
            {'message': 'Отзыв успешно отправлен и будет опубликован после проверки модератором'},
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def filter_by_rating(self, request):
        """Фильтрация отзывов по рейтингу"""
        rating_min = request.query_params.get('min', 1)
        rating_max = request.query_params.get('max', 5)
        
        queryset = self.queryset.filter(
            rating__gte=rating_min,
            rating__lte=rating_max
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='published')
    def published(self, request):
        """Получение только опубликованных отзывов"""
        queryset = self.queryset.filter(is_published=True)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
        
    @action(detail=False, methods=['get'], url_path='featured')
    def featured(self, request):
        """Получение избранных отзывов для главной страницы
        Возвращает 5 верифицированных отзывов с высшим рейтингом"""
        queryset = self.queryset.filter(
            is_published=True,
            is_verified=True,
            rating__gte=4
        ).order_by('-rating', '-created_at')[:5]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TransactionHistoryView(generics.ListAPIView):
    """
    Возвращает историю транзакций для аутентифицированного пользователя.
    """
    serializer_class = TransactionHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Возвращает транзакции текущего пользователя,
        оптимизируя запросы с помощью select_related и prefetch_related.
        """
        user = self.request.user
        return Transaction.objects.filter(user=user).select_related(
            'crypto'
        ).prefetch_related(
            'exchange',
            'deposit',
            'withdrawal'
        ).order_by('-timestamp')
