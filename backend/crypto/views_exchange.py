from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Cryptocurrency, UserWallet, ExchangePair, SystemWallet
from transactions.models import Transaction, Exchange
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import uuid
import logging

logger = logging.getLogger(__name__)

class ExchangeView(APIView):
    """
    API для обмена криптовалют
    """
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        """
        Создает запрос на обмен криптовалют
        
        Параметры:
        - from_currency: символ исходной валюты
        - to_currency: символ целевой валюты
        - amount: сумма в исходной валюте
        - custom_fee_percentage: пользовательская комиссия (опционально)
        """
        try:
            # Получаем данные из запроса
            from_currency = request.data.get('from_currency')
            to_currency = request.data.get('to_currency')
            amount = request.data.get('amount')
            custom_fee_percentage = request.data.get('custom_fee_percentage')
            
            # Валидация входных данных
            if not all([from_currency, to_currency, amount]):
                return Response({
                    'error': 'Не все обязательные поля заполнены',
                    'required_fields': ['from_currency', 'to_currency', 'amount']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                amount = Decimal(amount)
                if amount <= 0:
                    return Response({'error': 'Сумма должна быть положительной'}, status=status.HTTP_400_BAD_REQUEST)
            except:
                return Response({'error': 'Некорректная сумма'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Проверяем, что валюты существуют
            try:
                from_crypto = Cryptocurrency.objects.get(symbol=from_currency, is_active=True)
                to_crypto = Cryptocurrency.objects.get(symbol=to_currency, is_active=True)
            except Cryptocurrency.DoesNotExist:
                return Response({'error': 'Одна из валют не найдена или неактивна'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Проверяем, что пара обмена существует и активна
            try:
                exchange_pair = ExchangePair.objects.get(
                    from_crypto=from_crypto,
                    to_crypto=to_crypto,
                    is_active=True
                )
            except ExchangePair.DoesNotExist:
                return Response({'error': 'Данная пара обмена не поддерживается'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Получаем кошельки пользователя
            try:
                from_wallet = UserWallet.objects.get(user=request.user, crypto=from_crypto)
                to_wallet, created = UserWallet.objects.get_or_create(
                    user=request.user,
                    crypto=to_crypto,
                    defaults={
                        'balance': 0,
                        'available_balance': 0,
                        'address': f'virtual-{to_crypto.symbol.lower()}-{request.user.id}'
                    }
                )
            except UserWallet.DoesNotExist:
                return Response({'error': 'У вас нет кошелька для исходной валюты'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Проверяем достаточность средств
            if from_wallet.available_balance < amount:
                return Response({
                    'error': 'Недостаточно средств',
                    'available': float(from_wallet.available_balance),
                    'required': float(amount)
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Проверяем минимальную и максимальную сумму обмена
            if amount < from_crypto.min_amount:
                return Response({
                    'error': f'Минимальная сумма для обмена: {from_crypto.min_amount} {from_crypto.symbol}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if amount > from_crypto.max_amount:
                return Response({
                    'error': f'Максимальная сумма для обмена: {from_crypto.max_amount} {from_crypto.symbol}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Получаем курс обмена
            exchange_rate = self._get_exchange_rate(from_crypto.symbol, to_crypto.symbol)
            
            # Определяем комиссию
            fee_percentage = from_crypto.fee_percentage
            
            # Если указана пользовательская комиссия и она больше стандартной
            if custom_fee_percentage is not None:
                try:
                    custom_fee = Decimal(custom_fee_percentage)
                    if custom_fee > fee_percentage:
                        fee_percentage = custom_fee
                except:
                    pass  # Используем стандартную комиссию
            
            # Рассчитываем комиссию
            fee_amount = (amount * fee_percentage) / Decimal('100.0')
            
            # Рассчитываем сумму к получению
            to_amount = (amount - fee_amount) * exchange_rate
            
            # Проверяем наличие системного кошелька для целевой валюты
            if to_crypto.is_system:
                try:
                    system_wallet = SystemWallet.objects.get(crypto=to_crypto)
                    if system_wallet.available_balance < to_amount:
                        return Response({'error': 'Недостаточно ликвидности для обмена'}, status=status.HTTP_400_BAD_REQUEST)
                except SystemWallet.DoesNotExist:
                    return Response({'error': 'Системный кошелек не настроен'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Создаем запись об обмене
            exchange = Exchange.objects.create(
                user=request.user,
                from_wallet=from_wallet,
                to_wallet=to_wallet,
                from_amount=amount,
                to_amount=to_amount,
                fee=fee_amount,
                fee_percentage=fee_percentage,
                exchange_rate=exchange_rate,
                status='processing'
            )
            
            # Обрабатываем обмен
            self._process_exchange(exchange)
            
            return Response({
                'success': True,
                'exchange_id': exchange.exchange_id,
                'from_amount': float(amount),
                'from_currency': from_crypto.symbol,
                'to_amount': float(to_amount),
                'to_currency': to_crypto.symbol,
                'fee': float(fee_amount),
                'fee_percentage': float(fee_percentage),
                'exchange_rate': float(exchange_rate),
                'status': exchange.status
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Ошибка при обмене валют: {e}", exc_info=True)
            return Response({'error': 'Произошла ошибка при обработке запроса'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_exchange_rate(self, from_currency, to_currency):
        """
        Получает курс обмена между валютами
        В реальном проекте здесь будет запрос к API для получения актуального курса
        """
        # Упрощенные курсы для демонстрации
        rates = {
            'RUB_BTC': Decimal('0.0000005'),  # 1 RUB = 0.0000005 BTC
            'RUB_ETH': Decimal('0.000008'),   # 1 RUB = 0.000008 ETH
            'RUB_USDT': Decimal('0.01'),      # 1 RUB = 0.01 USDT
            
            'USD_BTC': Decimal('0.00003'),    # 1 USD = 0.00003 BTC
            'USD_ETH': Decimal('0.0005'),     # 1 USD = 0.0005 ETH
            'USD_USDT': Decimal('1.0'),       # 1 USD = 1 USDT
            
            'EUR_BTC': Decimal('0.000035'),   # 1 EUR = 0.000035 BTC
            'EUR_ETH': Decimal('0.00055'),    # 1 EUR = 0.00055 ETH
            'EUR_USDT': Decimal('1.1'),       # 1 EUR = 1.1 USDT
            
            'BTC_USDT': Decimal('30000'),     # 1 BTC = 30000 USDT
            'ETH_USDT': Decimal('2000'),      # 1 ETH = 2000 USDT
            'BTC_ETH': Decimal('15'),         # 1 BTC = 15 ETH
            'ETH_BTC': Decimal('0.066667'),   # 1 ETH = 0.066667 BTC
            
            'USDT_RUB': Decimal('100'),       # 1 USDT = 100 RUB
            'USDT_USD': Decimal('1.0'),       # 1 USDT = 1 USD
            'USDT_EUR': Decimal('0.91'),      # 1 USDT = 0.91 EUR
            
            'BTC_RUB': Decimal('3000000'),    # 1 BTC = 3000000 RUB
            'ETH_RUB': Decimal('200000'),     # 1 ETH = 200000 RUB
            
            'BTC_USD': Decimal('30000'),      # 1 BTC = 30000 USD
            'ETH_USD': Decimal('2000'),       # 1 ETH = 2000 USD
            
            'BTC_EUR': Decimal('27300'),      # 1 BTC = 27300 EUR
            'ETH_EUR': Decimal('1820'),       # 1 ETH = 1820 EUR
        }
        
        rate_key = f"{from_currency}_{to_currency}"
        return rates.get(rate_key, Decimal('1.0'))
    
    @transaction.atomic
    def _process_exchange(self, exchange):
        """
        Обрабатывает обмен валют
        """
        try:
            # Проверяем, что обмен в статусе processing
            if exchange.status != 'processing':
                return
            
            # Блокируем средства на исходном кошельке
            exchange.from_wallet.available_balance -= exchange.from_amount
            exchange.from_wallet.locked_balance += exchange.from_amount
            exchange.from_wallet.save()
            
            # Создаем транзакцию списания
            from_transaction = Transaction.objects.create(
                user=exchange.user,
                transaction_id=uuid.uuid4(),
                type='exchange_out',
                status='completed',
                amount=exchange.from_amount,
                fee=exchange.fee,
                crypto=exchange.from_wallet.crypto,
                notes=f"Обмен {exchange.from_amount} {exchange.from_wallet.crypto.symbol} на {exchange.to_amount} {exchange.to_wallet.crypto.symbol}"
            )
            
            # Создаем транзакцию пополнения
            to_transaction = Transaction.objects.create(
                user=exchange.user,
                transaction_id=uuid.uuid4(),
                type='exchange_in',
                status='completed',
                amount=exchange.to_amount,
                fee=0,  # Комиссия уже учтена
                crypto=exchange.to_wallet.crypto,
                notes=f"Получено из обмена {exchange.from_amount} {exchange.from_wallet.crypto.symbol}"
            )
            
            # Разблокируем и списываем средства с исходного кошелька
            exchange.from_wallet.locked_balance -= exchange.from_amount
            exchange.from_wallet.save()
            
            # Пополняем целевой кошелек
            exchange.to_wallet.available_balance += exchange.to_amount
            exchange.to_wallet.save()
            
            # Если целевая валюта системная, обновляем системный кошелек
            if exchange.to_wallet.crypto.is_system:
                system_wallet = SystemWallet.objects.get(crypto=exchange.to_wallet.crypto)
                system_wallet.available_balance -= exchange.to_amount
                system_wallet.save()
            
            # Обновляем статус обмена
            exchange.status = 'completed'
            exchange.completed_at = timezone.now()
            exchange.save()
            
            # Логируем успешный обмен
            logger.info(f"Успешный обмен: {exchange.user.username}, {exchange.from_amount} {exchange.from_wallet.crypto.symbol} -> {exchange.to_amount} {exchange.to_wallet.crypto.symbol}")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке обмена {exchange.exchange_id}: {e}", exc_info=True)
            
            # Возвращаем средства на исходный кошелек
            exchange.from_wallet.available_balance += exchange.from_amount
            exchange.from_wallet.locked_balance -= exchange.from_amount
            exchange.from_wallet.save()
            
            # Обновляем статус обмена
            exchange.status = 'failed'
            exchange.save()
            
            raise
