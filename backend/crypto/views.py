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

from .models import (Cryptocurrency, CryptoPrice, ExchangePair, UserWallet,
                    InvestmentPlan, UserInvestment, CardDeposit)
from .serializers import (
    CryptocurrencySerializer, CryptoPriceSerializer, ExchangePairSerializer,
    UserWalletSerializer, ExchangeCalculatorSerializer, InvestmentPlanSerializer,
    UserInvestmentSerializer, CardDepositSerializer
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


class InvestmentPlanViewSet(viewsets.ModelViewSet):
    """API для работы с инвестиционными планами"""
    queryset = InvestmentPlan.objects.filter(is_active=True)
    serializer_class = InvestmentPlanSerializer
    permission_classes = [AllowAny]
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
    
    def create(self, request, *args, **kwargs):
        """Создание новой инвестиции"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Получаем данные из запроса
        plan_id = serializer.validated_data.get('plan').id
        wallet_id = serializer.validated_data.get('wallet').id
        amount = serializer.validated_data.get('amount')
        
        # Проверяем, что кошелек принадлежит пользователю
        wallet = get_object_or_404(UserWallet, id=wallet_id, user=request.user)
        plan = get_object_or_404(InvestmentPlan, id=plan_id, is_active=True)
        
        # Проверяем, что валюты кошелька и плана совпадают
        if wallet.crypto.id != plan.crypto.id:
            return Response(
                {"error": f"Кошелек должен быть в той же валюте, что и план ({plan.crypto.symbol})"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем минимальную и максимальную сумму
        if amount < plan.min_investment:
            return Response(
                {"error": f"Минимальная сумма инвестиции: {plan.min_investment} {plan.crypto.symbol}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if amount > plan.max_investment:
            return Response(
                {"error": f"Максимальная сумма инвестиции: {plan.max_investment} {plan.crypto.symbol}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем, что на балансе достаточно средств
        if wallet.available_balance < amount:
            return Response(
                {"error": f"Недостаточно средств на балансе. Доступно: {wallet.available_balance} {wallet.crypto.symbol}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Создаем инвестицию
        investment = serializer.save(user=request.user)
        
        # Обновляем баланс кошелька
        wallet.available_balance -= amount
        wallet.locked_balance += amount
        wallet.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
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
    
    def create(self, request, *args, **kwargs):
        """Создание нового пополнения"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Получаем данные из запроса
        wallet_id = serializer.validated_data.get('wallet').id
        amount = serializer.validated_data.get('amount')
        currency = serializer.validated_data.get('currency')
        
        # Проверяем, что кошелек принадлежит пользователю
        wallet = get_object_or_404(UserWallet, id=wallet_id, user=request.user)
        
        # Получаем текущий курс криптовалюты к USD
        latest_price = CryptoPrice.objects.filter(crypto=wallet.crypto).order_by('-timestamp').first()
        if not latest_price:
            return Response(
                {"error": "Не удалось получить текущий курс криптовалюты"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Здесь должен быть запрос к сервису обмена валют для получения курса фиатной валюты к USD
        # Для простоты используем фиксированный курс
        fiat_to_usd_rate = 0.01  # Примерный курс RUB к USD
        if currency == 'USD':
            fiat_to_usd_rate = 1.0
        elif currency == 'EUR':
            fiat_to_usd_rate = 1.1  # Примерный курс EUR к USD
        
        # Рассчитываем количество криптовалюты
        usd_amount = amount * fiat_to_usd_rate
        crypto_amount = usd_amount / latest_price.price_usd
        
        # Рассчитываем комиссию (примерно 1%)
        fee_percentage = 1.0
        fee_amount = (amount * fee_percentage) / 100
        
        # Создаем запись о пополнении
        deposit = serializer.save(
            user=request.user,
            crypto_amount=crypto_amount,
            exchange_rate=latest_price.price_usd,
            fee=fee_amount,
            status='processing'  # В реальном приложении здесь был бы запрос к платежному шлюзу
        )
        
        # В реальном приложении здесь был бы редирект на страницу оплаты
        # Для демонстрации сразу подтверждаем платеж и зачисляем средства
        deposit.status = 'completed'
        deposit.completed_at = timezone.now()
        deposit.payment_id = f"demo-{uuid.uuid4().hex[:8]}"
        deposit.card_last4 = '1234'  # В реальном приложении это были бы данные от платежного шлюза
        deposit.card_brand = 'Visa'
        deposit.save()
        
        # Зачисляем средства на баланс кошелька
        wallet.balance += crypto_amount
        wallet.available_balance += crypto_amount
        wallet.save()
        
        return Response({
            "message": "Пополнение успешно завершено",
            "deposit": CardDepositSerializer(deposit).data
        }, status=status.HTTP_201_CREATED)
    
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
