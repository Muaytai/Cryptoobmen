from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.db.models import Q, F, Sum
from decimal import Decimal
import requests
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from django.db import transaction
from .models import (Cryptocurrency, CryptoPrice, ExchangePair, UserWallet,
                    InvestmentPlan, UserInvestment, CardDeposit)
from transactions.models import Transaction as TX, Exchange as TransactionExchange, Deposit, Withdrawal, Review
from .serializers import (
    CryptocurrencySerializer, CryptoPriceSerializer, ExchangePairSerializer,
    UserWalletSerializer, ExchangeCalculatorSerializer, InvestmentPlanSerializer,
    UserInvestmentSerializer, CardDepositSerializer
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
            latest_price = CryptoPrice.objects.filter(crypto=wallet.crypto).order_by('-timestamp').first()
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


class CardDepositViewSet(viewsets.ModelViewSet):
    """АРI для пополнения кошелька с банковской карты"""
    serializer_class = CardDepositSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Пользователь может видеть только свои пополнения"""
        return CardDeposit.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Этот ViewSet для CardDeposit также требует доработки
        - Интеграция с платежной системой (если не эмуляция)
        - Создание транзакции типа "deposit"
        - Обновление баланса UserWallet ПОСЛЕ успешного платежа
        ... (пропущена сложная логика)"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Статистика по пополнениям пользователя"""
        deposits = CardDeposit.objects.filter(user=request.user)
        
        # Статистика по завершенным пополнениям
        completed_deposits = deposits.filter(status='completed')
        completed_count = completed_deposits.count()
        completed_amount = completed_deposits.aggregate(total=Sum('amount'))['total'] or 0
        completed_crypto = completed_deposits.aggregate(total=Sum('crypto_amount'))['total'] or 0
        
        # Статистика по обрабатываемым пополнениям
        processing_deposits = deposits.filter(status='processing')
        processing_count = processing_deposits.count()
        processing_amount = processing_deposits.aggregate(total=Sum('amount'))['total'] or 0
        
        # Статистика по неудачным пополнениям
        failed_deposits = deposits.filter(status__in=['failed', 'cancelled'])
        failed_count = failed_deposits.count()
        failed_amount = failed_deposits.aggregate(total=Sum('amount'))['total'] or 0
        
        # Общая статистика
        total_count = deposits.count()
        total_amount = deposits.aggregate(total=Sum('amount'))['total'] or 0
        
        return Response({
            "completed_deposits": {
                "count": completed_count,
                "total_amount": completed_amount,
                "total_crypto": completed_crypto
            },
            "processing_deposits": {
                "count": processing_count,
                "total_amount": processing_amount
            },
            "failed_deposits": {
                "count": failed_count,
                "total_amount": failed_amount
            },
            "total_deposits": {
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


class FiatDepositView(APIView):
    """
    Эмулирует пополнение фиатного (USD) баланса пользователя.
    Принимает {'amount': '100.00'}
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        amount_str = request.data.get('amount')
        if not amount_str:
            return Response({"error": "Amount is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = Decimal(amount_str)
        except Exception: 
            return Response({"error": "Invalid amount format."}, status=status.HTTP_400_BAD_REQUEST)

        if amount <= 0:
            return Response({"error": "Amount must be positive."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        usd_currency, _ = Cryptocurrency.objects.get_or_create(
            symbol="USD",
            defaults={'name': "US Dollar", 'currency_type': 'fiat', 'is_active': True}
        )
        user_wallet, _ = UserWallet.objects.get_or_create(
            user=user, currency=usd_currency,
            defaults={'balance': Decimal('0.0'), 'available_balance': Decimal('0.0')}
        )
        
        user_wallet.balance += amount
        user_wallet.available_balance += amount
        user_wallet.save()

        card_deposit = CardDeposit.objects.create(
            user=user, wallet=user_wallet, amount=amount,
            currency=usd_currency.symbol, status='completed',
        )
        
        tx = TX.objects.create(
            user=user, type='deposit', status='completed',
            amount=amount, crypto=usd_currency, 
            notes=f"Fiat deposit emulation via card deposit ID: {card_deposit.deposit_id}"
        )

        return Response(
            {"message": f"Successfully deposited {amount} {usd_currency.symbol}.",
             "wallet_balance": user_wallet.balance,
             "card_deposit_id": card_deposit.deposit_id,
             "transaction_id": tx.transaction_id
             },
            status=status.HTTP_200_OK
        )


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
            return Response({"error": "Missing required fields: from_symbol, to_symbol, amount_from."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            amount_from = Decimal(amount_from_str)
        except Exception:
            return Response({"error": "Invalid amount_from format."}, status=status.HTTP_400_BAD_REQUEST)

        if amount_from <= 0:
            return Response({"error": "Amount_from must be positive."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        try:
            currency_from = Cryptocurrency.objects.get(symbol=from_symbol, is_active=True)
            currency_to = Cryptocurrency.objects.get(symbol=to_symbol, is_active=True)
        except Cryptocurrency.DoesNotExist:
            return Response({"error": "One or both currencies not found or not active."},
                            status=status.HTTP_404_NOT_FOUND)

        if currency_from == currency_to:
            return Response({"error": "Cannot exchange a currency for itself."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            wallet_from = UserWallet.objects.get(user=user, currency=currency_from, is_system_wallet=False)
        except UserWallet.DoesNotExist:
            return Response({"error": f"Wallet for {from_symbol} not found for this user."},
                            status=status.HTTP_404_NOT_FOUND)
        
        wallet_to, _ = UserWallet.objects.get_or_create(
            user=user, currency=currency_to, is_system_wallet=False,
            defaults={'balance': Decimal('0.0'), 'available_balance': Decimal('0.0')}
        )

        if wallet_from.available_balance < amount_from:
            return Response({"error": f"Insufficient available balance for {from_symbol}."},
                            status=status.HTTP_400_BAD_REQUEST)

        rates = get_exchange_rates()
        if rates is None: # Означает ошибку при запросе к CoinGecko
            return Response({"error": "Could not fetch exchange rates. Exchange temporarily unavailable."},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)
        if not rates: # Означает, что CoinGecko вернул пустой ответ (например, все coingecko_id неверны)
            return Response({"error": "Exchange rate provider returned no data for the requested currencies."},
                            status=status.HTTP_404_NOT_FOUND)

        rate_from_to_usd = None
        if currency_from.currency_type == 'crypto' and currency_from.coingecko_id in rates:
            rate_from_to_usd = Decimal(str(rates[currency_from.coingecko_id].get('usd', 0)))
        elif currency_from.symbol == 'USD':
            rate_from_to_usd = Decimal('1.0')
        
        if rate_from_to_usd is None or rate_from_to_usd <= 0:
            return Response({"error": f"Could not get USD exchange rate for {from_symbol} from provider or it is invalid."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        rate_to_to_usd = None
        if currency_to.currency_type == 'crypto' and currency_to.coingecko_id in rates:
            rate_to_to_usd = Decimal(str(rates[currency_to.coingecko_id].get('usd', 0)))
        elif currency_to.symbol == 'USD':
            rate_to_to_usd = Decimal('1.0')

        if rate_to_to_usd is None or rate_to_to_usd <= 0:
            return Response({"error": f"Could not get USD exchange rate for {to_symbol} from provider or it is invalid."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        effective_rate = rate_from_to_usd / rate_to_to_usd
        amount_to = amount_from * effective_rate
        
        amount_to_final = amount_to # Пока без комиссий
        # Примерные данные по комиссии, если бы она была:
        # fee_percentage_decimal = Decimal('0.002') # 0.2%
        # fee_amount_target = amount_to * fee_percentage_decimal
        # amount_to_final = amount_to - fee_amount_target
        # fee_db_percentage = fee_percentage_decimal * 100
        # fee_db_amount = fee_amount_target

        wallet_from.balance -= amount_from
        wallet_from.available_balance -= amount_from
        wallet_from.save()

        wallet_to.balance += amount_to_final
        wallet_to.available_balance += amount_to_final
        wallet_to.save()

        tx_notes = f"Exchange {amount_from} {from_symbol} to {amount_to_final:.8f} {to_symbol} at rate {effective_rate:.8f} {to_symbol}/{from_symbol}"
        tx = TX.objects.create(
            user=user, type='exchange', status='completed',
            amount=amount_from, crypto=currency_from, notes=tx_notes
        )
        
        exchange_record = TransactionExchange.objects.create(
            user=user, transaction=tx, from_crypto=currency_from,
            to_crypto=currency_to, from_amount=amount_from,
            to_amount=amount_to_final, rate=effective_rate,
            # Поля для комиссии в модели transactions.Exchange:
            # fee_percentage=fee_db_percentage if 'fee_db_percentage' in locals() else Decimal('0.0'), 
            # fee_amount=fee_db_amount if 'fee_db_amount' in locals() else Decimal('0.0')
            fee_percentage=Decimal('0.0'), # Заглушка
            fee_amount=Decimal('0.0')    # Заглушка
        )

        return Response({
            "message": "Exchange successful.",
            "from_currency": from_symbol, "to_currency": to_symbol,
            "amount_from": amount_from, "amount_to": f"{amount_to_final:.8f}",
            "rate": f"{effective_rate:.8f}", "transaction_id": tx.transaction_id,
            "exchange_id": exchange_record.id
        }, status=status.HTTP_200_OK)
