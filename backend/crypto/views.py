from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from decimal import Decimal
from rest_framework.views import APIView
from django.db import transaction
from .models import (
    Cryptocurrency, CryptoPrice, ExchangePair, UserWallet, ExchangeOrder, CommissionWallet
)
from transactions.models import Transfer
from transactions.models import Transaction as TX, Exchange as TransactionExchange
from .serializers import (
    CryptocurrencySerializer, CryptoPriceSerializer, ExchangePairSerializer,
    UserWalletSerializer, ExchangeCalculatorSerializer,
    TransferSerializer, ExchangeOrderSerializer, CommissionWalletSerializer
)
from .services import get_exchange_rates
from transactions.services import ExchangeService


class CryptocurrencyViewSet(viewsets.ModelViewSet):
    """API для работы с криптовалютами"""
    queryset = Cryptocurrency.objects.all()
    serializer_class = CryptocurrencySerializer
    permission_classes = [AllowAny]
    
    def get_permissions(self):
        """Определяем права доступа в зависимости от действия"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Разрешаем site-admin и staff управлять криптовалютами
            from rest_framework.permissions import IsAuthenticated
            return [IsAuthenticated]
        return [AllowAny()]
    
    def get_queryset(self):
        """Для не-админов показываем только активные криптовалюты"""
        if self.request.user.is_authenticated and (
            self.request.user.is_staff or 
            getattr(self.request.user, 'is_site_administrator', lambda: False)()
        ):
            return Cryptocurrency.objects.all()
        return Cryptocurrency.objects.filter(is_active=True)
    
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
                    "coingecko_id": crypto_obj.coingecko_id,
                    "currency_type": crypto_obj.currency_type,
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
            # Получаем последнюю цену для криптовалюты
            crypto = wallet.currency
            if crypto.symbol == 'USDT':
                try:
                    # Пробуем найти криптовалюту Tether для получения корректной цены
                    tether_crypto = Cryptocurrency.objects.filter(coingecko_id='tether').first()
                    if tether_crypto:
                        latest_price = CryptoPrice.objects.filter(crypto=tether_crypto).order_by('-timestamp').first()
                    else:
                        latest_price = None
                except Cryptocurrency.DoesNotExist: # Этот блок теперь можно убрать, но оставим для безопасности
                    latest_price = None
            else:
                latest_price = CryptoPrice.objects.filter(crypto=crypto).order_by('-timestamp').first()
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
        serializer.is_valid(raise_exception=True)

        from_crypto = serializer.validated_data['from_crypto']
        to_crypto = serializer.validated_data['to_crypto']
        amount = serializer.validated_data['amount']

        result = ExchangeService.calculate_by_currencies(from_crypto, to_crypto, amount)

        return Response({
            "from_amount": amount,
            "from_crypto": CryptocurrencySerializer(from_crypto).data,
            "to_amount": round(result['to_amount'], 8),
            "to_crypto": CryptocurrencySerializer(to_crypto).data,
            "rate": round(result['rate'], 8),
            "fee_percentage": result['fee_percent'],
            "fee_amount_original_currency": round(result['fee_amount'], 8),
        })




class TransferViewSet(viewsets.ReadOnlyModelViewSet):
    """Просмотр переводов пользователя (депозиты/выводы)."""
    serializer_class = TransferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transfer.objects.filter(user=self.request.user).order_by('-created_at')


class ExchangeOrderViewSet(viewsets.ModelViewSet):
    """Создание и просмотр ордеров обмена пользователя."""
    serializer_class = ExchangeOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ExchangeOrder.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status='pending')


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
            to_currency = Cryptocurrency.objects.filter(symbol=to_symbol).first()
            if not to_currency:
                return Response({'error': f'Валюта {to_symbol} не найдена.'}, status=status.HTTP_404_NOT_FOUND)
            to_wallet, _ = UserWallet.objects.get_or_create(user=user, currency=to_currency)
        except Cryptocurrency.DoesNotExist:
            return Response({'error': 'Одна из указанных валют не найдена.'}, status=status.HTTP_404_NOT_FOUND)

        if from_wallet.available_balance < amount_from:
            return Response({'error': 'Недостаточно средств на балансе для обмена.'},
                            status=status.HTTP_400_BAD_REQUEST)

        from_crypto_coingecko_id = from_wallet.currency.coingecko_id
        if from_wallet.currency.symbol == 'USDT':
            from_crypto_coingecko_id = 'tether'
        
        to_crypto_coingecko_id = to_wallet.currency.coingecko_id
        if to_wallet.currency.symbol == 'USDT':
            to_crypto_coingecko_id = 'tether'

        live_rates = get_exchange_rates(['usd'])

        # Ожидаем курс каждой валюты к USD и строим кросс-курс
        if not live_rates:
            return Response({"error": "Не удалось получить актуальный курс для указанной пары."},
                            status=status.HTTP_400_BAD_REQUEST)

        from_rate_data = live_rates.get(from_crypto_coingecko_id) or {}
        to_rate_data = live_rates.get(to_crypto_coingecko_id) or {}
        from_usd_rate = from_rate_data.get('usd')
        to_usd_rate = to_rate_data.get('usd')

        if not from_usd_rate or not to_usd_rate:
            return Response({"error": "Не удалось получить актуальный курс для указанной пары."},
                            status=status.HTTP_400_BAD_REQUEST)

        rate = Decimal(str(from_usd_rate)) / Decimal(str(to_usd_rate))
        amount_to = amount_from * rate

        # Комиссия платформы
        fee_percentage = from_wallet.currency.fee_percentage
        fee_amount = amount_from * (fee_percentage / Decimal('100'))
        net_amount = amount_from - fee_amount
        amount_to = net_amount * rate

        # Списываем full amount, но в лицо кошелька переводим комиссию в CommissionWallet
        from_wallet.balance -= amount_from
        from_wallet.available_balance -= amount_from

        from_wallet.save()

        # Зачисляем комиссию
        commission_wallet, _ = CommissionWallet.objects.get_or_create(currency=from_wallet.currency)
        commission_wallet.balance += fee_amount
        commission_wallet.save()

        # Создаём основную транзакцию
        tx = TX.objects.create(
            user=user,
            type='exchange',
            status='completed',
            amount=amount_from,
            fee=fee_amount,
            crypto=from_wallet.currency
        )
        # Создаём запись об обмене
        exchange_tx = TransactionExchange.objects.create(
            user=user,
            transaction=tx,
            from_crypto=from_wallet.currency,
            to_crypto=to_wallet.currency,
            from_amount=amount_from,
            to_amount=amount_to,
            rate=rate,
            fee_percentage=fee_percentage,
            fee_amount=fee_amount
        )

        to_wallet.balance += amount_to
        to_wallet.available_balance += amount_to
        to_wallet.save()

        return Response({
            'success': 'Обмен успешно выполнен.',
            'from_wallet': UserWalletSerializer(from_wallet).data,
            'to_wallet': UserWalletSerializer(to_wallet).data,
            'exchange_details': {
                'id': exchange_tx.id,
                'from': exchange_tx.from_crypto.symbol,
                'to': exchange_tx.to_crypto.symbol,
                'amount_from': exchange_tx.from_amount,
                'amount_to': exchange_tx.to_amount,
                'rate': exchange_tx.rate,
                'timestamp': exchange_tx.timestamp,
                'fee_amount': exchange_tx.fee_amount,
                'fee_percentage': exchange_tx.fee_percentage,
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
            source_currency = Cryptocurrency.objects.filter(symbol__iexact=source_symbol).first()
            target_currency = Cryptocurrency.objects.filter(symbol__iexact=target_symbol).first()

            if not source_currency or not target_currency:
                return Response({"error": "One or both of the specified currency symbols do not exist."}, status=status.HTTP_404_NOT_FOUND)

            # The service function fetches all available rates against USD.
            all_rates = get_exchange_rates() 

            if all_rates is None:
                return Response(
                    {"error": "Could not connect to the exchange rate service."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Get the USD rate for the source currency
            source_coingecko_id = source_currency.coingecko_id
            if source_currency.symbol == 'USDT':
                source_coingecko_id = 'tether'
            source_rate_data = all_rates.get(source_coingecko_id)
            if not source_rate_data or 'usd' not in source_rate_data:
                return Response({"error": f"Rate for source currency {source_symbol} not available."}, status=status.HTTP_404_NOT_FOUND)
            source_rate_usd = Decimal(str(source_rate_data['usd']))

            # Get the USD rate for the target currency
            target_coingecko_id = target_currency.coingecko_id
            if target_currency.symbol == 'USDT':
                target_coingecko_id = 'tether'
            target_rate_data = all_rates.get(target_coingecko_id)
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

            raise ValueError("Invalid exchange rate")
            
        except (KeyError, ValueError) as e:
            return Response({"error": f"Не удалось получить актуальный курс для обмена. {e}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)




# ------------------------------------------------------------------
#   Админ: системные кошельки (on-chain адреса) + комиссионные
# ------------------------------------------------------------------


class SystemWalletViewSet(viewsets.ReadOnlyModelViewSet):
    """Список системных кошельков платформы (виден только администратору)."""

    serializer_class = UserWalletSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return UserWallet.objects.filter(is_system_wallet=True).order_by('currency__name')


class CommissionWalletViewSet(viewsets.ReadOnlyModelViewSet):
    """Список комиссионных кошельков (накопленная прибыль)."""

    serializer_class = CommissionWalletSerializer
    permission_classes = [IsAdminUser]

    queryset = CommissionWallet.objects.all().order_by('currency__name')
