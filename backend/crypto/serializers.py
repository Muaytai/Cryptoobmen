from rest_framework import serializers
from decimal import Decimal
from .models import (
    Cryptocurrency, CryptoPrice, ExchangePair, UserWallet, ExchangeOrder, CommissionWallet
)
from transactions.models import Transfer

class CryptocurrencySerializer(serializers.ModelSerializer):
    """Сериализатор для криптовалют"""
    
    class Meta:
        model = Cryptocurrency
        fields = ['id', 'name', 'symbol', 'icon', 'is_active', 
                  'min_exchange_amount', 'max_exchange_amount',
                  'currency_type', 'network', 'coingecko_id', 'requires_memo']
        read_only_fields = ['id']


class CryptoPriceSerializer(serializers.ModelSerializer):
    """Сериализатор для цен криптовалют"""
    crypto_name = serializers.ReadOnlyField(source='crypto.name')
    crypto_symbol = serializers.ReadOnlyField(source='crypto.symbol')
    
    class Meta:
        model = CryptoPrice
        fields = ['id', 'crypto', 'crypto_name', 'crypto_symbol', 'price_usd', 'price_btc', 
                 'price_eth', 'market_cap', 'volume_24h', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class ExchangePairSerializer(serializers.ModelSerializer):
    """Сериализатор для пар обмена"""
    from_crypto_symbol = serializers.ReadOnlyField(source='from_crypto.symbol')
    to_crypto_symbol = serializers.ReadOnlyField(source='to_crypto.symbol')
    from_crypto_name = serializers.ReadOnlyField(source='from_crypto.name')
    to_crypto_name = serializers.ReadOnlyField(source='to_crypto.name')
    
    class Meta:
        model = ExchangePair
        fields = ['id', 'from_crypto', 'from_crypto_symbol', 'from_crypto_name',
                 'to_crypto', 'to_crypto_symbol', 'to_crypto_name',
                 'is_active', 'custom_fee_percentage', 'min_from_amount', 'max_from_amount']
        read_only_fields = ['id']


class CryptocurrencySimpleSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для отображения информации о валюте в кошельке."""
    currency_type = serializers.SerializerMethodField()

    class Meta:
        model = Cryptocurrency
        fields = ['id', 'name', 'symbol', 'icon', 'currency_type', 'network']

    def get_currency_type(self, obj):
        """Возвращает полное название типа валюты, например 'Cryptocurrency' или 'Fiat'."""
        return obj.get_currency_type_display()


class UserWalletSerializer(serializers.ModelSerializer):
    """Сериализатор для кошельков пользователя, включая тип валюты."""
    currency = CryptocurrencySimpleSerializer(read_only=True)
    
    class Meta:
        model = UserWallet
        fields = ['id', 'currency', 'balance', 'available_balance', 'locked_balance', 'is_active']


class ExchangeCalculatorSerializer(serializers.Serializer):
    """Сериализатор для расчета обмена валют"""
    from_crypto_id = serializers.IntegerField()
    to_crypto_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=24, decimal_places=8)
    
    def validate(self, data):
        """Валидация данных для расчета обмена"""
        try:
            from_crypto = Cryptocurrency.objects.get(id=data['from_crypto_id'], is_active=True)
            to_crypto = Cryptocurrency.objects.get(id=data['to_crypto_id'], is_active=True)
            
            # Проверяем, существует ли пара обмена
            exchange_pair = ExchangePair.objects.filter(
                from_crypto=from_crypto,
                to_crypto=to_crypto,
                is_active=True
            ).first()
            
            if not exchange_pair:
                raise serializers.ValidationError("Данная пара обмена недоступна")
            
            # Проверяем минимальную и максимальную сумму
            # Используем min_from_amount/max_from_amount из ExchangePair если они заданы, иначе из Cryptocurrency
            min_amount = exchange_pair.min_from_amount if exchange_pair.min_from_amount is not None else from_crypto.min_exchange_amount
            max_amount = exchange_pair.max_from_amount if exchange_pair.max_from_amount is not None else from_crypto.max_exchange_amount
            
            # Важно: Убедимся, что min_amount и max_amount не None перед сравнением
            if min_amount is not None and data['amount'] < min_amount:
                raise serializers.ValidationError(f"Минимальная сумма для обмена: {min_amount} {from_crypto.symbol}")
            
            if max_amount is not None and data['amount'] > max_amount:
                raise serializers.ValidationError(f"Максимальная сумма для обмена: {max_amount} {from_crypto.symbol}")
            
            data['from_crypto'] = from_crypto
            data['to_crypto'] = to_crypto
            data['exchange_pair'] = exchange_pair # Сохраняем найденную пару для дальнейшего использования
            
            return data
        except Cryptocurrency.DoesNotExist:
            raise serializers.ValidationError("Одна из валют не найдена или неактивна")




class DepositInfoRequestSerializer(serializers.Serializer):
    """
    Сериализатор для валидации запроса на получение информации для депозита.
    """
    currency_symbol = serializers.CharField(max_length=10)
    network = serializers.CharField(max_length=50)

    def validate_currency_symbol(self, value):
        """Проверяет, что такая криптовалюта существует и активна."""
        if not Cryptocurrency.objects.filter(symbol__iexact=value, is_active=True).exists():
            raise serializers.ValidationError(f"Криптовалюта {value} не найдена или неактивна.")
        return value.upper()

    def validate_network(self, value):
        """Проверяет, что такая сеть поддерживается (опционально, можно расширить)."""
        # Здесь можно добавить более сложную логику, например, сверку с доступными сетями для валюты
        return value


class TransferSerializer(serializers.ModelSerializer):
    """Сериализатор переводов (депозиты/выводы)."""

    currency = CryptocurrencySimpleSerializer(read_only=True)
    currency_id = serializers.PrimaryKeyRelatedField(
        queryset=Cryptocurrency.objects.all(), source='currency', write_only=True
    )

    class Meta:
        model = Transfer
        fields = [
            'id', 'type', 'status',
            'currency', 'currency_id', 'amount', 'tx_hash',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'tx_hash', 'created_at', 'updated_at']


class ExchangeOrderSerializer(serializers.ModelSerializer):
    """Сериализатор ордеров обмена."""

    from_currency = CryptocurrencySimpleSerializer(read_only=True)
    to_currency = CryptocurrencySimpleSerializer(read_only=True)

    from_currency_id = serializers.PrimaryKeyRelatedField(
        queryset=Cryptocurrency.objects.all(), source='from_currency', write_only=True
    )
    to_currency_id = serializers.PrimaryKeyRelatedField(
        queryset=Cryptocurrency.objects.all(), source='to_currency', write_only=True
    )

    class Meta:
        model = ExchangeOrder
        fields = [
            'id', 'status', 'user',
            'from_currency', 'from_currency_id', 'from_amount',
            'to_currency', 'to_currency_id', 'to_amount',
            'rate', 'fee_percent', 'fee_amount',
            'created_at', 'executed_at'
        ]
        read_only_fields = ['id', 'status', 'user', 'to_amount', 'rate', 'fee_amount', 'created_at', 'executed_at']

    def create(self, validated_data):
        """Простая реализация расчёта курса для тестирования.
        В боевом коде должен использоваться сервис обмена, здесь достаточно фиксированного курса 1:1."""
        from_amount = validated_data.get('from_amount')
        from_currency = validated_data.get('from_currency')
        to_currency = validated_data.get('to_currency')

        # Заглушка: курс 1:1
        rate = Decimal('1')
        to_amount = from_amount * rate

        validated_data['rate'] = rate
        validated_data['to_amount'] = to_amount

        return super().create(validated_data)


class PerformExchangeSerializer(serializers.Serializer):
    """Сериализатор для выполнения обмена."""
    from_crypto_id = serializers.IntegerField()
    to_crypto_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=24, decimal_places=8)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Сумма должна быть положительной.")
        return value


# --- CommissionWalletSerializer


class CommissionWalletSerializer(serializers.ModelSerializer):
    """Сериализатор для внутренних комиссионных кошельков (виден только админам)."""

    currency = CryptocurrencySimpleSerializer(read_only=True)

    class Meta:
        model = CommissionWallet
        fields = ['id', 'currency', 'balance', 'is_active']
