from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.db.models import Q, F, Sum, OuterRef, Subquery
from decimal import Decimal
import requests
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from django.db import transaction
from .models import (Cryptocurrency, CryptoPrice, ExchangePair, UserWallet,
                    InvestmentPlan, UserInvestment)
from transactions.models import Transaction as TX, Exchange as TransactionExchange, Deposit, Withdrawal, Review
from .serializers import (
    CryptocurrencySerializer, CryptoPriceSerializer, ExchangePairSerializer,
    UserWalletSerializer, ExchangeCalculatorSerializer, InvestmentPlanSerializer,
    UserInvestmentSerializer, PerformExchangeSerializer
)
from .services import get_exchange_rates


class CryptocurrencyViewSet(viewsets.ReadOnlyModelViewSet):
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
        latest_price_ids = []
        active_crypto_ids = Cryptocurrency.objects.filter(is_active=True).values_list('id', flat=True)
        
        for crypto_id in active_crypto_ids:
            latest_price = CryptoPrice.objects.filter(crypto_id=crypto_id).order_by('-timestamp').first()
            if latest_price:
                latest_price_ids.append(latest_price.id)
        
        if not latest_price_ids:
            return CryptoPrice.objects.none()
            
        return CryptoPrice.objects.filter(id__in=latest_price_ids).order_by('-timestamp') # Added order_by for consistency
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Возвращает последние цены для всех криптовалют"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class LatestCryptoPricesView(APIView):
    """
    Возвращает последние актуальные цены для всех активных криптовалют
    в указанных валютах.
    Принимает GET-параметр `vs_currencies` (через запятую), например: ?vs_currencies=usd,eur,btc
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        vs_currencies_str = request.query_params.get('vs_currencies', 'usd')
        vs_currencies = [currency.strip().lower() for currency in vs_currencies_str.split(',')]
        
        # Получаем самые свежие курсы из нашего сервиса
        rates = get_exchange_rates(vs_currencies=vs_currencies)

        if rates is None:
            return Response(
                {"error": "Could not fetch exchange rates from the provider."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Нам нужны ID криптовалют, чтобы затем найти их в БД
        coingecko_ids = list(rates.keys())
        
        # Находим соответствующие объекты Cryptocurrency
        crypto_map = {
            c.coingecko_id: c for c in Cryptocurrency.objects.filter(coingecko_id__in=coingecko_ids)
        }
        
        # Формируем ответ, обогащая его данными из нашей БД
        response_data = []
        for coingecko_id, price_data in rates.items():
            crypto_obj = crypto_map.get(coingecko_id)
            if crypto_obj:
                response_data.append({
                    "crypto_id": crypto_obj.id,
                    "name": crypto_obj.name,
                    "symbol": crypto_obj.symbol,
                    "prices": price_data, # {'usd': 123, 'eur': 456}
                })

        return Response(response_data)


class ExchangePairViewSet(viewsets.ReadOnlyModelViewSet):
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
        return UserWallet.objects.filter(user=self.request.user, is_system_wallet=False)
    
    def get_permissions(self):
        """Определяем права доступа в зависимости от действия"""
        if self.action in ['create', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Привязываем кошелек к текущему пользователю при создании через API"""
        serializer.save(user=self.request.user, is_system_wallet=False)
    
    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Возвращает суммарный баланс в долларах"""
        wallets = self.get_queryset()
        total_usd_balance = 0
        
        for wallet in wallets:
            # Получаем последнюю цену для криптовалюты
            latest_price = CryptoPrice.objects.filter(crypto=wallet.currency).order_by('-timestamp').first()
            if latest_price:
                total_usd_balance += wallet.balance * latest_price.price_usd
        
        return Response({
            "total_usd_balance": round(total_usd_balance, 2)
        })


class ExchangeCalculatorAPIView(APIView):
    """API для расчета обмена валют"""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Рассчитывает сумму к получению при обмене"""
        serializer = ExchangeCalculatorSerializer(data=request.data)
        if serializer.is_valid():
            from_crypto = serializer.validated_data['from_crypto']
            to_crypto = serializer.validated_data['to_crypto']
            amount = serializer.validated_data['amount']
            
            live_rates = get_exchange_rates() # Возвращает {'coingecko_id': {'usd': rate}, ...}

            if live_rates is None:
                return Response({"error": "Не удалось связаться с сервисом курсов валют. Попробуйте позже."},
                                status=status.HTTP_503_SERVICE_UNAVAILABLE)
            if not live_rates:
                return Response({"error": "Сервис курсов валют не вернул данные. Возможно, нет активных валют с coingecko_id."},
                                status=status.HTTP_404_NOT_FOUND)

            from_usd_rate = None
            if from_crypto.currency_type == 'crypto':
                # Используем coingecko_id и извлекаем 'usd'
                if from_crypto.coingecko_id and from_crypto.coingecko_id in live_rates:
                    rate_data = live_rates[from_crypto.coingecko_id]
                    if 'usd' in rate_data:
                        from_usd_rate = Decimal(str(rate_data['usd']))
            elif from_crypto.symbol == 'USD':
                from_usd_rate = Decimal('1.0')

            to_usd_rate = None
            if to_crypto.currency_type == 'crypto':
                # Используем coingecko_id и извлекаем 'usd'
                if to_crypto.coingecko_id and to_crypto.coingecko_id in live_rates:
                    rate_data = live_rates[to_crypto.coingecko_id]
                    if 'usd' in rate_data:
                        to_usd_rate = Decimal(str(rate_data['usd']))
            elif to_crypto.symbol == 'USD':
                to_usd_rate = Decimal('1.0')

            if from_usd_rate is None or from_usd_rate <= 0:
                # Добавил coingecko_id в сообщение об ошибке для ясности
                return Response({"error": f"Не удалось получить актуальный курс для {from_crypto.symbol} (ID: {from_crypto.coingecko_id}) или курс некорректен."},
                                status=status.HTTP_400_BAD_REQUEST)
            
            if to_usd_rate is None or to_usd_rate <= 0:
                # Добавил coingecko_id в сообщение об ошибке для ясности
                return Response({"error": f"Не удалось получить актуальный курс для {to_crypto.symbol} (ID: {to_crypto.coingecko_id}) или курс некорректен."},
                                status=status.HTTP_400_BAD_REQUEST)
            
            rate = from_usd_rate / to_usd_rate
            
            fee_percentage_from_crypto = from_crypto.fee_percentage if hasattr(from_crypto, 'fee_percentage') else Decimal('0.0')
            fee_amount_from = amount * (fee_percentage_from_crypto / Decimal('100.0'))
            amount_after_fee = amount - fee_amount_from
            to_amount = amount_after_fee * rate
            
            return Response({
                "from_amount": amount,
                "from_crypto": CryptocurrencySerializer(from_crypto).data,
                "to_amount": round(to_amount, 8),
                "to_crypto": CryptocurrencySerializer(to_crypto).data,
                "rate": round(rate, 8),
                "fee_percentage": fee_percentage_from_crypto,
                "fee_amount_original_currency": round(fee_amount_from, 8),
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InvestmentPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """API для работы с инвестиционными планами"""
    queryset = InvestmentPlan.objects.filter(is_active=True)
    serializer_class = InvestmentPlanSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description', 'crypto__name', 'crypto__symbol']
    
    def get_permissions(self):
        """Определяем права доступа в зависимости от действия"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]
    
    @action(detail=False, methods=['get'])
    def by_crypto(self, request):
        """Возвращает инвестиционные планы для конкретной криптовалюты"""
        crypto_id = request.query_params.get('crypto_id')
        if not crypto_id:
            return Response({"error": "Необходимо указать crypto_id"}, status=status.HTTP_400_BAD_REQUEST)
        
        plans = InvestmentPlan.objects.filter(crypto_id=crypto_id, is_active=True)
        serializer = self.get_serializer(plans, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def calculate_return(self, request, pk=None):
        """Рассчитывает ожидаемый доход для заданной суммы инвестиции"""
        plan = self.get_object()
        amount = request.query_params.get('amount')
        
        if not amount:
            return Response({"error": "Необходимо указать сумму инвестиции"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            amount = Decimal(amount)
        except:
            return Response({"error": "Некорректная сумма инвестиции"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем минимальную и максимальную сумму
        if amount < plan.min_investment:
            return Response({"error": f"Минимальная сумма инвестиции: {plan.min_investment} {plan.crypto.symbol}"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        if amount > plan.max_investment:
            return Response({"error": f"Максимальная сумма инвестиции: {plan.max_investment} {plan.crypto.symbol}"},
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Рассчитываем ожидаемый доход
        interest_decimal = plan.interest_rate / Decimal('100.0')
        expected_return = amount * interest_decimal
        total_return = amount + expected_return
        
        # Получаем текущий курс к USD
        latest_price = CryptoPrice.objects.filter(crypto=plan.crypto).order_by('-timestamp').first()
        usd_value = 0
        if latest_price:
            usd_value = amount * latest_price.price_usd
        
        return Response({
            "plan": InvestmentPlanSerializer(plan).data,
            "investment_amount": amount,
            "interest_rate": plan.interest_rate,
            "expected_return": expected_return,
            "total_return": total_return,
            "duration_days": plan.get_duration_in_days(),
            "usd_value": round(usd_value, 2)
        })


class UserInvestmentViewSet(viewsets.ModelViewSet):
    """АРI для работы с инвестициями пользователей"""
    serializer_class = UserInvestmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Пользователь может видеть только свои инвестиции"""
        return UserInvestment.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Здесь должна быть логика создания инвестиции:
        - Проверка баланса пользователя
        - Списание средств с кошелька UserWallet и блокировка (или создание locked_balance)
        - Расчет expected_return, end_date
        - Создание транзакции типа "investment_start"
        Этот ViewSet требует доработки для реальной работы"""
        plan = serializer.validated_data.get('plan')
        amount = serializer.validated_data.get('amount')
        # ... (пропущена сложная логика)
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def withdraw_early(self, request, pk=None):
        """Досрочное закрытие инвестиции"""
        investment = self.get_object()
        
        # Проверяем, что инвестиция активна
        if investment.status != 'active':
            return Response(
                {"error": "Эта инвестиция уже закрыта или отменена"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем, разрешен ли досрочный вывод
        if not investment.plan.early_withdrawal_allowed:
            return Response(
                {"error": "Досрочный вывод не разрешен для этого плана"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Рассчитываем прогресс и фактический доход
        progress = investment.get_progress_percentage() / 100.0
        expected_return = investment.expected_return
        
        # Рассчитываем доход с учетом прогресса и комиссии за досрочный вывод
        actual_return = expected_return * progress
        
        # Применяем комиссию за досрочный вывод
        fee_percentage = investment.plan.early_withdrawal_fee
        fee_amount = (actual_return * fee_percentage) / 100
        actual_return -= fee_amount
        
        # Обновляем инвестицию
        investment.status = 'withdrawn'
        investment.actual_return = actual_return
        investment.completed_date = timezone.now()
        investment.save()
        
        # Возвращаем средства на баланс кошелька
        wallet = investment.wallet
        return_amount = investment.amount + actual_return
        
        wallet.locked_balance -= investment.amount
        wallet.available_balance += return_amount
        wallet.save()
        
        return Response({
            "message": "Инвестиция успешно закрыта",
            "investment": UserInvestmentSerializer(investment).data,
            "withdrawn_amount": return_amount,
            "fee_amount": fee_amount
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Статистика по инвестициям пользователя"""
        # Получаем все инвестиции пользователя
        investments = UserInvestment.objects.filter(user=request.user)
        
        # Статистика по активным инвестициям
        active_investments = investments.filter(status='active')
        active_count = active_investments.count()
        active_amount = active_investments.aggregate(total=Sum('amount'))['total'] or 0
        
        # Статистика по завершенным инвестициям
        completed_investments = investments.filter(status__in=['completed', 'withdrawn'])
        completed_count = completed_investments.count()
        completed_amount = completed_investments.aggregate(total=Sum('amount'))['total'] or 0
        total_return = completed_investments.aggregate(total=Sum('actual_return'))['total'] or 0
        
        # Общая статистика
        total_count = investments.count()
        total_amount = investments.aggregate(total=Sum('amount'))['total'] or 0
        
        return Response({
            "active_investments": {
                "count": active_count,
                "total_amount": active_amount,
                "expected_return": active_investments.aggregate(total=Sum('expected_return'))['total'] or 0
            },
            "completed_investments": {
                "count": completed_count,
                "total_amount": completed_amount,
                "total_return": total_return
            },
            "total_investments": {
                "count": total_count,
                "total_amount": total_amount
            }
        })


class UserBalancesView(generics.ListAPIView):
    """
    Возвращает список кошельков и балансов для аутентифицированного пользователя.
    """
    serializer_class = UserWalletSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Возвращаем только кошельки текущего пользователя, исключая системные
        return UserWallet.objects.filter(user=self.request.user, is_system_wallet=False).order_by('currency__name') # Добавил сортировку


class ExchangeRatesView(APIView):
    """
    Возвращает текущие курсы обмена для активных криптовалют к USD.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        rates_from_service = get_exchange_rates() # Это {'coingecko_id': {'usd': rate}, ...}
        if rates_from_service is None: 
            return Response({"error": "Could not fetch exchange rates from the provider."},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        processed_rates = {} # Будем преобразовывать в {'SYMBOL': rate}
        # Нам нужны только те валюты, которые есть и в ответе сервиса, и активны в нашей БД
        active_currencies_in_db = Cryptocurrency.objects.filter(
            coingecko_id__in=rates_from_service.keys(), 
            currency_type='crypto',
            is_active=True
        )
        # Создаем карту coingecko_id -> symbol для этих валют
        currency_map = {curr.coingecko_id: curr.symbol for curr in active_currencies_in_db}

        for coingecko_id, data in rates_from_service.items():
            symbol = currency_map.get(coingecko_id) # Получаем наш символ по coingecko_id
            if symbol and 'usd' in data:
                processed_rates[symbol] = data['usd'] # Ключ - наш символ, значение - курс
        
        if not processed_rates: 
             return Response({"message": "No active exchange rates found for configured/matched currencies or provider returned no data."},
                            status=status.HTTP_404_NOT_FOUND)

        return Response(processed_rates) # Возвращаем {'SYMBOL': rate}


class ExchangeCurrencyView(APIView):
    """
    Выполняет обмен одной валюты на другую для аутентифицированного пользователя.
    Принимает: {'from_symbol': 'BTC', 'to_symbol': 'USD', 'amount_from': '0.1'}
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        from_symbol = request.data.get('from_symbol')
        to_symbol = request.data.get('to_symbol')
        amount_from_str = request.data.get('amount_from')

        if not all([from_symbol, to_symbol, amount_from_str]):
            return Response({'error': 'Необходимо указать from_symbol, to_symbol и amount_from.'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            amount_from = Decimal(amount_from_str)
            if amount_from <= 0:
                raise ValueError("Сумма должна быть положительной")
        except (ValueError, TypeError):
            return Response({'error': 'Некорректная сумма для обмена.'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        try:
            from_wallet = get_object_or_404(UserWallet, user=user, currency__symbol=from_symbol)
            to_wallet, _ = UserWallet.objects.get_or_create(user=user, currency=get_object_or_404(Cryptocurrency,
                                                                                                    symbol=to_symbol))
        except Cryptocurrency.DoesNotExist:
            return Response({'error': 'Одна из указанных валют не найдена.'}, status=status.HTTP_404_NOT_FOUND)

        if from_wallet.available_balance < amount_from:
            return Response({'error': 'Недостаточно средств на балансе для обмена.'},
                            status=status.HTTP_400_BAD_REQUEST)

        live_rates = get_exchange_rates([from_wallet.currency.coingecko_id], [to_wallet.currency.coingecko_id])

        if not live_rates or from_wallet.currency.coingecko_id not in live_rates or to_wallet.currency.coingecko_id not in live_rates[from_wallet.currency.coingecko_id]:
            return Response({"error": "Не удалось получить актуальный курс для указанной пары."},
                            status=status.HTTP_400_BAD_REQUEST)
        
        rate = Decimal(str(live_rates[from_wallet.currency.coingecko_id][to_wallet.currency.coingecko_id]))
        amount_to = amount_from * rate

        # Списываем средства с одного кошелька и зачисляем на другой
        from_wallet.balance -= amount_from
        from_wallet.available_balance -= amount_from
        to_wallet.balance += amount_to
        to_wallet.available_balance += amount_to

        from_wallet.save()
        to_wallet.save()

        # Создаем запись об обмене
        exchange = TransactionExchange.objects.create(
            user=user,
            from_currency=from_wallet.currency,
            to_currency=to_wallet.currency,
            amount_from=amount_from,
            amount_to=amount_to,
            rate=rate
        )

        return Response({
            'success': 'Обмен успешно выполнен.',
            'from_wallet': UserWalletSerializer(from_wallet).data,
            'to_wallet': UserWalletSerializer(to_wallet).data,
            'exchange_details': {
                'id': exchange.id,
                'from': exchange.from_currency.symbol,
                'to': exchange.to_currency.symbol,
                'amount_from': exchange.amount_from,
                'amount_to': exchange.amount_to,
                'rate': exchange.rate,
                'timestamp': exchange.timestamp
            }
        }, status=status.HTTP_200_OK)


class ExchangeRateView(APIView):
    """
    View to get the exchange rate between two currencies.
    Expects query parameters: ?source_currency_symbol=RUB&target_currency_symbol=BTC
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        from decimal import Decimal, InvalidOperation

        source_symbol = request.query_params.get('source_currency_symbol')
        target_symbol = request.query_params.get('target_currency_symbol')

        if not source_symbol or not target_symbol:
            return Response(
                {"error": "Both source_currency_symbol and target_currency_symbol are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            source_currency = Cryptocurrency.objects.get(symbol__iexact=source_symbol)
            target_currency = Cryptocurrency.objects.get(symbol__iexact=target_symbol)

            # The service function fetches all available rates against USD.
            all_rates = get_exchange_rates() 

            if all_rates is None:
                return Response(
                    {"error": "Could not connect to the exchange rate service."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Get the USD rate for the source currency
            source_rate_data = all_rates.get(source_currency.coingecko_id)
            if not source_rate_data or 'usd' not in source_rate_data:
                return Response({"error": f"Rate for source currency {source_symbol} not available."}, status=status.HTTP_404_NOT_FOUND)
            source_rate_usd = Decimal(str(source_rate_data['usd']))

            # Get the USD rate for the target currency
            target_rate_data = all_rates.get(target_currency.coingecko_id)
            if not target_rate_data or 'usd' not in target_rate_data:
                return Response({"error": f"Rate for target currency {target_symbol} not available."}, status=status.HTTP_404_NOT_FOUND)
            target_rate_usd = Decimal(str(target_rate_data['usd']))
            
            if target_rate_usd == 0:
                 return Response({"error": f"Target currency rate for {target_symbol} is zero, cannot divide."}, status=status.HTTP_400_BAD_REQUEST)

            # Calculate the cross rate
            cross_rate = source_rate_usd / target_rate_usd

            return Response({"rate": cross_rate}, status=status.HTTP_200_OK)

        except Cryptocurrency.DoesNotExist:
            return Response({"error": "One or both of the specified currency symbols do not exist."}, status=status.HTTP_404_NOT_FOUND)
        except (InvalidOperation, TypeError) as e:
            print(f"Error in ExchangeRateView (Decimal conversion): {e}")
            return Response({"error": "Error converting currency rate to number."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print(f"Error in ExchangeRateView: {e}")
            return Response({"error": "An unexpected error occurred while retrieving the exchange rate."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def perform_exchange_view(request):
    """
    Выполняет обмен валюты для пользователя.
    """
    serializer = PerformExchangeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data
    from_crypto_id = validated_data['from_crypto_id']
    to_crypto_id = validated_data['to_crypto_id']
    amount = validated_data['amount']
    user = request.user

    # Используем select_for_update для блокировки строк на время транзакции
    try:
        from_wallet = UserWallet.objects.select_for_update().get(user=user, currency_id=from_crypto_id)
        to_wallet, _ = UserWallet.objects.select_for_update().get_or_create(
            user=user, currency_id=to_crypto_id, defaults={'balance': 0}
        )
    except UserWallet.DoesNotExist:
        return Response({"error": "Исходный кошелек не найден."}, status=status.HTTP_404_NOT_FOUND)

    # Проверка доступного баланса
    if from_wallet.available_balance < amount:
        return Response({"error": "Недостаточно средств на балансе."}, status=status.HTTP_400_BAD_REQUEST)

    # Получение актуальных курсов
    try:
        from_crypto = Cryptocurrency.objects.get(id=from_crypto_id)
        to_crypto = Cryptocurrency.objects.get(id=to_crypto_id)
        live_rates = get_exchange_rates(vs_currencies=['usd'])
        
        from_usd_rate = Decimal(str(live_rates[from_crypto.coingecko_id]['usd']))
        to_usd_rate = Decimal(str(live_rates[to_crypto.coingecko_id]['usd']))
        
        if from_usd_rate <= 0 or to_usd_rate <= 0:
            raise ValueError("Invalid exchange rate")
            
    except (KeyError, ValueError) as e:
        return Response({"error": f"Не удалось получить актуальный курс для обмена. {e}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # Расчет суммы к получению
    rate = from_usd_rate / to_usd_rate
    to_amount = amount * rate # Упрощенный расчет без комиссии для примера

    # Обновление балансов
    from_wallet.balance -= amount
    from_wallet.available_balance -= amount
    to_wallet.balance += to_amount
    to_wallet.available_balance += to_amount

    from_wallet.save()
    to_wallet.save()

    # Создание записи о транзакции обмена
    exchange_tx = TransactionExchange.objects.create(
        user=user,
        from_currency=from_crypto,
        to_currency=to_crypto,
        amount_from=amount,
        amount_to=to_amount,
        rate=rate,
        status='completed'
    )

    return Response({
        "success": True,
        "message": "Обмен успешно выполнен.",
        "exchange_id": exchange_tx.id
    }, status=status.HTTP_200_OK)
