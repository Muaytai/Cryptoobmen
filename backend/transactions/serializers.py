from rest_framework import serializers
from .models import Transaction, Exchange, Deposit, Withdrawal, Review
from crypto.models import Cryptocurrency, UserWallet, CryptoPrice
from crypto.serializers import CryptocurrencySerializer
from django.db import transaction as db_transaction
from decimal import Decimal
from django.utils import timezone


class TransactionSerializer(serializers.ModelSerializer):
    """Сериализатор для транзакций"""
    crypto_name = serializers.ReadOnlyField(source='crypto.name')
    crypto_symbol = serializers.ReadOnlyField(source='crypto.symbol')
    type_display = serializers.ReadOnlyField(source='get_type_display')
    status_display = serializers.ReadOnlyField(source='get_status_display')
    
    class Meta:
        model = Transaction
        fields = ['id', 'transaction_id', 'type', 'status', 'amount', 'fee',
                 'crypto', 'crypto_name', 'crypto_symbol', 'timestamp',
                 'tx_hash', 'notes', 'type_display', 'status_display']
        read_only_fields = ['id', 'transaction_id', 'timestamp']


class ExchangeSerializer(serializers.ModelSerializer):
    """Сериализатор для обмена валют"""
    transaction = TransactionSerializer(read_only=True)
    from_crypto_name = serializers.ReadOnlyField(source='from_crypto.name')
    from_crypto_symbol = serializers.ReadOnlyField(source='from_crypto.symbol')
    to_crypto_name = serializers.ReadOnlyField(source='to_crypto.name')
    to_crypto_symbol = serializers.ReadOnlyField(source='to_crypto.symbol')
    
    class Meta:
        model = Exchange
        fields = ['id', 'transaction', 'from_crypto', 'from_crypto_name', 'from_crypto_symbol',
                 'to_crypto', 'to_crypto_name', 'to_crypto_symbol', 'from_amount',
                 'to_amount', 'rate', 'fee_percentage', 'fee_amount', 'timestamp']
        read_only_fields = ['id', 'transaction', 'timestamp']


class DepositSerializer(serializers.ModelSerializer):
    """Сериализатор для депозитов"""
    transaction = TransactionSerializer(read_only=True)
    wallet_crypto_symbol = serializers.ReadOnlyField(source='wallet.crypto.symbol')
    
    class Meta:
        model = Deposit
        fields = ['id', 'transaction', 'wallet', 'wallet_crypto_symbol', 'address',
                 'confirmed', 'confirmation_date']
        read_only_fields = ['id', 'transaction', 'confirmed', 'confirmation_date']


class WithdrawalSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода средств"""
    transaction = TransactionSerializer(read_only=True)
    wallet_crypto_symbol = serializers.ReadOnlyField(source='wallet.crypto.symbol')
    
    class Meta:
        model = Withdrawal
        fields = ['id', 'transaction', 'wallet', 'wallet_crypto_symbol', 'destination_address',
                 'is_2fa_confirmed', 'is_email_confirmed', 'confirmed_by_admin',
                 'rejected_reason', 'confirmation_date']
        read_only_fields = ['id', 'transaction', 'confirmed_by_admin', 'rejected_reason',
                           'confirmation_date']


class ExchangeCreateSerializer(serializers.Serializer):
    """Сериализатор для создания обмена валют"""
    from_crypto_id = serializers.IntegerField()
    to_crypto_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=24, decimal_places=8)
    
    def validate(self, data):
        """Валидация данных для обмена"""
        user = self.context['request'].user
        
        try:
            from_crypto = Cryptocurrency.objects.get(id=data['from_crypto_id'], is_active=True)
            to_crypto = Cryptocurrency.objects.get(id=data['to_crypto_id'], is_active=True)
            
            # Проверяем наличие кошельков
            from_wallet = UserWallet.objects.get(user=user, crypto=from_crypto, is_active=True)
            to_wallet = UserWallet.objects.get(user=user, crypto=to_crypto, is_active=True)
            
            # Проверяем баланс
            if from_wallet.balance < data['amount']:
                raise serializers.ValidationError(f"Недостаточно средств. Баланс: {from_wallet.balance} {from_crypto.symbol}")
            
            # Получаем последние цены криптовалют
            from_price = CryptoPrice.objects.filter(crypto=from_crypto).order_by('-timestamp').first()
            to_price = CryptoPrice.objects.filter(crypto=to_crypto).order_by('-timestamp').first()
            
            if not from_price or not to_price:
                raise serializers.ValidationError("Не удалось получить текущие цены валют")
            
            # Рассчитываем курс обмена
            rate = from_price.price_usd / to_price.price_usd
            
            # Рассчитываем комиссию
            fee_percentage = from_crypto.fee_percentage
            fee_amount = (data['amount'] * fee_percentage) / 100
            
            # Рассчитываем сумму к получению
            to_amount = (data['amount'] - fee_amount) * rate
            
            data['from_crypto'] = from_crypto
            data['to_crypto'] = to_crypto
            data['from_wallet'] = from_wallet
            data['to_wallet'] = to_wallet
            data['rate'] = rate
            data['fee_percentage'] = fee_percentage
            data['fee_amount'] = fee_amount
            data['to_amount'] = to_amount
            
            return data
        except Cryptocurrency.DoesNotExist:
            raise serializers.ValidationError("Одна из валют не найдена или неактивна")
        except UserWallet.DoesNotExist:
            raise serializers.ValidationError("Кошелек не найден")
    
    def create(self, validated_data):
        """Создает обмен валют"""
        user = self.context['request'].user
        
        from_crypto = validated_data['from_crypto']
        to_crypto = validated_data['to_crypto']
        from_wallet = validated_data['from_wallet']
        to_wallet = validated_data['to_wallet']
        from_amount = validated_data['amount']
        to_amount = validated_data['to_amount']
        rate = validated_data['rate']
        fee_percentage = validated_data['fee_percentage']
        fee_amount = validated_data['fee_amount']
        
        with db_transaction.atomic():
            # Создаем транзакцию
            transaction = Transaction.objects.create(
                user=user,
                type='exchange',
                status='completed',
                amount=from_amount,
                fee=fee_amount,
                crypto=from_crypto,
                ip_address=self.context['request'].META.get('REMOTE_ADDR'),
                notes=f"Exchange from {from_amount} {from_crypto.symbol} to {to_amount} {to_crypto.symbol}"
            )
            
            # Создаем обмен
            exchange = Exchange.objects.create(
                user=user,
                transaction=transaction,
                from_crypto=from_crypto,
                to_crypto=to_crypto,
                from_amount=from_amount,
                to_amount=to_amount,
                rate=rate,
                fee_percentage=fee_percentage,
                fee_amount=fee_amount
            )
            
            # Обновляем балансы кошельков
            from_wallet.balance -= from_amount
            from_wallet.save()
            
            to_wallet.balance += to_amount
            to_wallet.save()
            
            return exchange


class WithdrawalCreateSerializer(serializers.Serializer):
    """Сериализатор для создания запроса на вывод средств"""
    crypto_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=24, decimal_places=8)
    destination_address = serializers.CharField(max_length=255)
    
    def validate(self, data):
        """Валидация данных для вывода"""
        user = self.context['request'].user
        
        try:
            crypto = Cryptocurrency.objects.get(id=data['crypto_id'], is_active=True)
            
            # Проверяем наличие кошелька
            wallet = UserWallet.objects.get(user=user, crypto=crypto, is_active=True)
            
            # Проверяем баланс
            if wallet.balance < data['amount']:
                raise serializers.ValidationError(f"Недостаточно средств. Баланс: {wallet.balance} {crypto.symbol}")
            
            # Проверяем минимальную сумму вывода
            if data['amount'] < crypto.min_amount:
                raise serializers.ValidationError(f"Минимальная сумма вывода: {crypto.min_amount} {crypto.symbol}")
            
            # Рассчитываем комиссию
            fee_percentage = crypto.fee_percentage
            fee_amount = (data['amount'] * fee_percentage) / 100
            
            # Проверяем, что сумма к выводу после комиссии положительная
            if data['amount'] - fee_amount <= 0:
                raise serializers.ValidationError("Сумма к выводу после комиссии должна быть положительной")
            
            data['crypto'] = crypto
            data['wallet'] = wallet
            data['fee_percentage'] = fee_percentage
            data['fee_amount'] = fee_amount
            
            return data
        except Cryptocurrency.DoesNotExist:
            raise serializers.ValidationError("Криптовалюта не найдена или неактивна")
        except UserWallet.DoesNotExist:
            raise serializers.ValidationError("Кошелек не найден")
    
    def create(self, validated_data):
        """Создает запрос на вывод средств"""
        user = self.context['request'].user
        
        crypto = validated_data['crypto']
        wallet = validated_data['wallet']
        amount = validated_data['amount']
        fee_amount = validated_data['fee_amount']
        destination_address = validated_data['destination_address']
        
        with db_transaction.atomic():
            # Создаем транзакцию
            transaction = Transaction.objects.create(
                user=user,
                type='withdrawal',
                status='pending',
                amount=amount,
                fee=fee_amount,
                crypto=crypto,
                ip_address=self.context['request'].META.get('REMOTE_ADDR'),
                notes=f"Withdrawal {amount} {crypto.symbol} to {destination_address}"
            )
            
            # Создаем вывод
            withdrawal = Withdrawal.objects.create(
                user=user,
                transaction=transaction,
                wallet=wallet,
                destination_address=destination_address
            )
            
            # Блокируем средства на кошельке
            wallet.balance -= amount
            wallet.save()
            
            return withdrawal


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор для модели отзывов"""
    user_name = serializers.ReadOnlyField(source='user.username')
    date = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'name', 'email', 'rating', 'content', 'is_verified', 
            'is_published', 'is_featured', 'created_at', 'updated_at', 
            'user', 'user_name', 'date'
        ]
        read_only_fields = ['user', 'is_verified', 'is_published', 'is_featured', 
                           'created_at', 'updated_at']
    
    def get_date(self, obj):
        """Возвращает дату в формате дд.мм.гггг"""
        return obj.created_at.strftime('%d.%m.%Y')


class ExchangeDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор для обмена (для вложенного представления)."""
    from_currency = CryptocurrencySerializer(read_only=True)
    to_currency = CryptocurrencySerializer(read_only=True)

    class Meta:
        model = Exchange
        fields = ['from_currency', 'to_currency', 'from_amount', 'to_amount', 'rate']


class DepositDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор для пополнения."""
    class Meta:
        model = Deposit
        fields = ['address', 'confirmed']


class WithdrawalDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор для вывода."""
    class Meta:
        model = Withdrawal
        fields = ['destination_address', 'is_email_confirmed', 'confirmed_by_admin']


class TransactionHistorySerializer(serializers.ModelSerializer):
    """Основной сериализатор для истории транзакций."""
    crypto = CryptocurrencySerializer(read_only=True)
    details = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'transaction_id', 'type', 'status', 'amount', 'fee',
            'crypto', 'timestamp', 'tx_hash', 'details'
        ]

    def get_details(self, obj):
        """Возвращает детали для конкретного типа транзакции."""
        if obj.type == 'exchange' and hasattr(obj, 'exchange_transaction'):
            return ExchangeDetailSerializer(obj.exchange_transaction).data
        if obj.type == 'deposit' and hasattr(obj, 'deposit_transaction'):
            return DepositDetailSerializer(obj.deposit_transaction).data
        if obj.type == 'withdrawal' and hasattr(obj, 'withdrawal_transaction'):
            return WithdrawalDetailSerializer(obj.withdrawal_transaction).data
        return None 