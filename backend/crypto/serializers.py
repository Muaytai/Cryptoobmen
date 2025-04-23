from rest_framework import serializers
from .models import Cryptocurrency, CryptoPrice, ExchangePair, UserWallet


class CryptocurrencySerializer(serializers.ModelSerializer):
    """Сериализатор для криптовалют"""
    
    class Meta:
        model = Cryptocurrency
        fields = ['id', 'name', 'symbol', 'icon', 'is_active', 'min_amount', 'max_amount', 'fee_percentage']
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


class UserWalletSerializer(serializers.ModelSerializer):
    """Сериализатор для кошельков пользователя"""
    crypto_name = serializers.ReadOnlyField(source='crypto.name')
    crypto_symbol = serializers.ReadOnlyField(source='crypto.symbol')
    crypto_icon = serializers.ImageField(source='crypto.icon', read_only=True)
    
    class Meta:
        model = UserWallet
        fields = ['id', 'crypto', 'crypto_name', 'crypto_symbol', 'crypto_icon',
                 'balance', 'address', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'crypto', 'balance', 'created_at', 'updated_at']


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
            min_amount = exchange_pair.min_from_amount or from_crypto.min_amount
            max_amount = exchange_pair.max_from_amount or from_crypto.max_amount
            
            if data['amount'] < min_amount:
                raise serializers.ValidationError(f"Минимальная сумма для обмена: {min_amount} {from_crypto.symbol}")
            
            if data['amount'] > max_amount:
                raise serializers.ValidationError(f"Максимальная сумма для обмена: {max_amount} {from_crypto.symbol}")
            
            data['from_crypto'] = from_crypto
            data['to_crypto'] = to_crypto
            data['exchange_pair'] = exchange_pair
            
            return data
        except Cryptocurrency.DoesNotExist:
            raise serializers.ValidationError("Одна из валют не найдена или неактивна") 