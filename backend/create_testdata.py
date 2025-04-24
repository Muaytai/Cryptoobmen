import os
import django
from decimal import Decimal

# Установка переменных окружения Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

# Импортируем модели
from crypto.models import Cryptocurrency, CryptoPrice, ExchangePair

def create_test_data():
    """
    Создает тестовые данные для проекта
    """
    # Создаем основные криптовалюты
    print("Создание тестовых криптовалют...")
    
    # Bitcoin
    btc, created = Cryptocurrency.objects.get_or_create(
        symbol='BTC',
        defaults={
            'name': 'Bitcoin',
            'is_active': True,
            'coingecko_id': 'bitcoin',
            'min_amount': Decimal('0.0001'),
            'max_amount': Decimal('10'),
            'fee_percentage': Decimal('0.5')
        }
    )
    
    # Ethereum
    eth, created = Cryptocurrency.objects.get_or_create(
        symbol='ETH',
        defaults={
            'name': 'Ethereum',
            'is_active': True,
            'coingecko_id': 'ethereum',
            'min_amount': Decimal('0.001'),
            'max_amount': Decimal('100'),
            'fee_percentage': Decimal('0.5')
        }
    )
    
    # USDT
    usdt, created = Cryptocurrency.objects.get_or_create(
        symbol='USDT',
        defaults={
            'name': 'Tether',
            'is_active': True,
            'coingecko_id': 'tether',
            'min_amount': Decimal('10'),
            'max_amount': Decimal('100000'),
            'fee_percentage': Decimal('0.5')
        }
    )
    
    # Создаем цены для криптовалют
    if not CryptoPrice.objects.filter(crypto=btc).exists():
        CryptoPrice.objects.create(
            crypto=btc,
            price_usd=Decimal('65000'),
            price_btc=Decimal('1'),
            price_eth=Decimal('25'),
            market_cap=Decimal('1250000000000'),
            volume_24h=Decimal('25000000000')
        )
    
    if not CryptoPrice.objects.filter(crypto=eth).exists():
        CryptoPrice.objects.create(
            crypto=eth,
            price_usd=Decimal('2600'),
            price_btc=Decimal('0.04'),
            price_eth=Decimal('1'),
            market_cap=Decimal('310000000000'),
            volume_24h=Decimal('15000000000')
        )
    
    if not CryptoPrice.objects.filter(crypto=usdt).exists():
        CryptoPrice.objects.create(
            crypto=usdt,
            price_usd=Decimal('1'),
            price_btc=Decimal('0.000015'),
            price_eth=Decimal('0.00038'),
            market_cap=Decimal('95000000000'),
            volume_24h=Decimal('60000000000')
        )
    
    # Создаем пары обмена
    print("Создание пар обмена...")
    # BTC -> ETH
    ExchangePair.objects.get_or_create(
        from_crypto=btc,
        to_crypto=eth,
        defaults={
            'is_active': True
        }
    )
    
    # ETH -> BTC
    ExchangePair.objects.get_or_create(
        from_crypto=eth,
        to_crypto=btc,
        defaults={
            'is_active': True
        }
    )
    
    # BTC -> USDT
    ExchangePair.objects.get_or_create(
        from_crypto=btc,
        to_crypto=usdt,
        defaults={
            'is_active': True
        }
    )
    
    # USDT -> BTC
    ExchangePair.objects.get_or_create(
        from_crypto=usdt,
        to_crypto=btc,
        defaults={
            'is_active': True
        }
    )
    
    # ETH -> USDT
    ExchangePair.objects.get_or_create(
        from_crypto=eth,
        to_crypto=usdt,
        defaults={
            'is_active': True
        }
    )
    
    # USDT -> ETH
    ExchangePair.objects.get_or_create(
        from_crypto=usdt,
        to_crypto=eth,
        defaults={
            'is_active': True
        }
    )
    
    print("Тестовые данные созданы!")

if __name__ == "__main__":
    create_test_data() 