
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
from crypto.gas_calculation import calculate_max_withdrawal_amount, calculate_withdrawal_total_cost
from .serializers import (
    TransactionSerializer, ExchangeSerializer, DepositSerializer,
    WithdrawalSerializer, ExchangeCreateSerializer, WithdrawalCreateSerializer,
    ReviewSerializer, TransactionHistorySerializer, AdminTransactionSerializer
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
    def admin_list(self, request):
        """Возвращает список всех транзакций для администраторов"""
        if not (request.user.is_staff or request.user.is_site_admin):
            return Response(
                {"error": "У вас нет прав для просмотра всех транзакций"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Получаем параметры фильтрации
        user_id = request.query_params.get('user_id')
        transaction_type = request.query_params.get('type')
        status_filter = request.query_params.get('status')
        crypto_id = request.query_params.get('crypto_id')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        search = request.query_params.get('search')
        
        # Базовый queryset с оптимизацией
        queryset = Transaction.objects.select_related(
            'user', 'crypto'
        ).prefetch_related(
            'exchange', 'deposit', 'withdrawal'
        ).order_by('-timestamp')
        
        # Применяем фильтры
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        if transaction_type:
            queryset = queryset.filter(type=transaction_type)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if crypto_id:
            queryset = queryset.filter(crypto_id=crypto_id)
        
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)
        
        if search:
            queryset = queryset.filter(
                Q(transaction_id__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__username__icontains=search) |
                Q(tx_hash__icontains=search) |
                Q(crypto__symbol__icontains=search)
            )
        
        # Пагинация
        page_size = int(request.query_params.get('page_size', 50))
        page = int(request.query_params.get('page', 1))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        transactions = queryset[start:end]
        total_count = queryset.count()
        
        serializer = AdminTransactionSerializer(transactions, many=True)
        
        return Response({
            'results': serializer.data,
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        })
    
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
    
    @action(detail=False, methods=['post'], url_path='max-amount')
    def get_max_withdrawal_amount(self, request):
        """Получает максимальную сумму вывода с учетом газа"""
        try:
            crypto_id = request.data.get('crypto_id')
            destination_address = request.data.get('destination_address')
            
            if crypto_id is None:
                return Response({'error': 'crypto_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Получаем криптовалюту
            try:
                crypto = Cryptocurrency.objects.get(id=crypto_id, is_active=True)
            except Cryptocurrency.DoesNotExist:
                return Response({'error': 'Cryptocurrency not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Получаем кошелек пользователя
            try:
                wallet = UserWallet.objects.get(user=request.user, currency=crypto, is_active=True)
            except UserWallet.DoesNotExist:
                return Response({'error': 'Wallet not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Рассчитываем максимальную сумму вывода с учетом газа
            max_withdrawal_info = calculate_max_withdrawal_amount(
                currency=crypto,
                user_balance=wallet.balance,
                destination_address=destination_address
            )
            
            return Response({
                'max_withdrawal': str(max_withdrawal_info['max_withdrawal']),
                'gas_cost': str(max_withdrawal_info['gas_cost']),
                'total_required': str(max_withdrawal_info['total_required']),
                'calculation_method': max_withdrawal_info['calculation_method'],
                'currency_symbol': crypto.symbol,
                'user_balance': str(wallet.balance)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': f'Error calculating max withdrawal amount: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='calculate-cost')
    def calculate_withdrawal_cost(self, request):
        """Рассчитывает стоимость вывода (сумма + газ + комиссия)"""
        try:
            crypto_id = request.data.get('crypto_id')
            amount = request.data.get('amount')
            destination_address = request.data.get('destination_address')
            
            if crypto_id is None or amount is None:
                return Response({'error': 'crypto_id and amount are required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Получаем криптовалюту
            try:
                crypto = Cryptocurrency.objects.get(id=crypto_id, is_active=True)
            except Cryptocurrency.DoesNotExist:
                return Response({'error': 'Cryptocurrency not found'}, status=status.HTTP_404_NOT_FOUND)
            
            from decimal import Decimal
            amount_decimal = Decimal(str(amount))
            
            # Рассчитываем общую стоимость вывода
            cost_info = calculate_withdrawal_total_cost(
                currency=crypto,
                withdrawal_amount=amount_decimal,
                destination_address=destination_address
            )
            
            return Response({
                'withdrawal_amount': str(cost_info['withdrawal_amount']),
                'gas_cost': str(cost_info['gas_cost']),
                'platform_fee': str(cost_info['platform_fee']),
                'total_cost': str(cost_info['total_cost']),
                'calculation_method': cost_info['calculation_method'],
                'currency_symbol': crypto.symbol
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': f'Error calculating withdrawal cost: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
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
        import logging
        logger = logging.getLogger(__name__)
        
        user = request.user
        currency_id = request.data.get('currency_id')
        network = request.data.get('network')  # Добавляем поддержку network
        
        logger.info(f"get_deposit_address: user={user.email}, currency_id={currency_id}, network={network}")
        logger.info(f"get_deposit_address: request.data={request.data}")
        logger.info(f"get_deposit_address: request.user.id={user.id}")

        if not currency_id:
            return Response({"error": "currency_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Если указана сеть, ищем валюту по символу и сети
            if network:
                # Ищем валюту по символу и сети (не только USDT)
                currency = Cryptocurrency.objects.get(symbol__iexact=currency_id, network=network)
                logger.info(f"get_deposit_address: found currency by symbol and network: {currency.symbol} (id={currency.id}, network={currency.network})")
            else:
                # Иначе ищем по ID (для обратной совместимости)
                try:
                    # Сначала пытаемся найти по ID (число)
                    currency_id_int = int(currency_id)
                    currency = Cryptocurrency.objects.get(id=currency_id_int)
                    logger.info(f"get_deposit_address: found currency by id: {currency.symbol} (id={currency.id}, network={currency.network})")
                except (ValueError, TypeError):
                    # Если не число, ищем по символу
                    currency = Cryptocurrency.objects.get(symbol__iexact=currency_id)
                    logger.info(f"get_deposit_address: found currency by symbol: {currency.symbol} (id={currency.id}, network={currency.network})")
            
            # Проверяем существующие кошельки пользователя для этой валюты
            existing_wallets = UserWallet.objects.filter(user=user, currency=currency)
            logger.info(f"get_deposit_address: found {existing_wallets.count()} existing wallets for user {user.email} and currency {currency.symbol} ({currency.network})")
            
            for wallet in existing_wallets:
                logger.info(f"get_deposit_address: wallet id={wallet.id}, address={wallet.deposit_address}, is_system={wallet.is_system_wallet}")
            
            # Если у пользователя несколько кошельков для одной валюты, выбираем тот, у которого есть адрес
            wallet = None
            created = False
            
            if existing_wallets.count() > 1:
                # Выбираем кошелек с адресом, если есть
                wallet_with_address = existing_wallets.filter(deposit_address__isnull=False).exclude(deposit_address='').first()
                if wallet_with_address:
                    wallet = wallet_with_address
                    logger.info(f"get_deposit_address: selected wallet with address id={wallet.id}, address={wallet.deposit_address}")
                else:
                    # Если нет кошелька с адресом, берем первый
                    wallet = existing_wallets.first()
                    logger.info(f"get_deposit_address: selected first wallet id={wallet.id}, address={wallet.deposit_address}")
            elif existing_wallets.count() == 1:
                wallet = existing_wallets.first()
                logger.info(f"get_deposit_address: found single wallet id={wallet.id}, address={wallet.deposit_address}")
            else:
                # Создаем новый кошелек только если не нашли существующий
                wallet = UserWallet.objects.create(user=user, currency=currency)
                created = True
                logger.info(f"get_deposit_address: created new wallet id={wallet.id}")

            # Проверяем, что адрес соответствует выбранной сети
            if wallet.deposit_address and not created:
                # ОТЛАДКА: Логируем ВСЁ перед проверками
                address = wallet.deposit_address
                logger.error(f"🔍 ADDRESS CHECK DEBUG:")
                logger.error(f"   Currency: {currency.symbol} (ID: {currency.id})")
                logger.error(f"   Network: '{currency.network}'")
                logger.error(f"   Address: '{address}'")
                logger.error(f"   Starts with 0x: {address.startswith('0x')}")
                logger.error(f"   Starts with T: {address.startswith('T')}")
                logger.error(f"   ERC20 check: {currency.network == 'ERC20'}")
                logger.error(f"   TRC20 check: {currency.network == 'TRC20'}")
                
                # Проверяем формат адреса для соответствия сети
                if currency.network == 'ERC20' and not address.startswith('0x'):
                    logger.error(f"🚨 CLEARING ADDRESS: ERC20 check failed!")
                    logger.warning(f"get_deposit_address: wallet {wallet.id} has non-ERC20 address {address} for ERC20 currency {currency.symbol}")
                    # Сбрасываем неправильный адрес
                    wallet.deposit_address = None
                    wallet.save()
                elif currency.network == 'TRC20' and not address.startswith('T'):
                    logger.error(f"🚨 CLEARING ADDRESS: TRC20 check failed!")
                    logger.warning(f"get_deposit_address: wallet {wallet.id} has non-TRC20 address {address} for TRC20 currency {currency.symbol}")
                    # Сбрасываем неправильный адрес
                    wallet.deposit_address = None
                    wallet.save()
                else:
                    logger.error(f"✅ ADDRESS CHECK PASSED - no clearing needed")

            # --- Новая унифицированная логика через DepositService ---
            from crypto.services_deposit import DepositService

            # DepositService сам обрабатывает создание/обновление адреса
            result = DepositService.get_deposit_info(
                user=user,
                currency_symbol=currency.symbol,
                network=currency.network
            )
            
            # Обрабатываем результат в зависимости от количества возвращаемых значений
            if len(result) == 4:
                address, memo, qr_code, gas_info = result
            else:
                # Обратная совместимость со старым форматом
                address, memo, qr_code = result
                gas_info = None

            # Убеждаемся, что memo не None для валют с requires_memo
            if currency.requires_memo and not memo:
                logger.warning(f"Currency {currency.symbol} requires memo but memo is None or empty")
                memo = None  # Явно устанавливаем None если memo отсутствует

            response_data = {
                'address': address,
                'memo': memo if memo else None,  # Явно устанавливаем None вместо пустой строки
                'qr_code': qr_code,
                'currency_symbol': currency.symbol,
                'network': currency.network,
                'requires_memo': currency.requires_memo  # Добавляем информацию о необходимости memo
            }
            
            # Логируем для отладки
            logger.info(f"Deposit address response for {currency.symbol}: memo={memo}, requires_memo={currency.requires_memo}")
            
            # Добавляем информацию о газе для валют без мемо
            if gas_info is not None:
                response_data['gas_info'] = gas_info
            
            return Response(response_data, status=status.HTTP_200_OK)

        except Cryptocurrency.DoesNotExist:
            logger.error(f"get_deposit_address: currency with id {currency_id} and network {network} not found")
            return Response({"error": "Currency not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"get_deposit_address: unexpected error: {e}", exc_info=True)
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

