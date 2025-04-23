import os
import django
import sys
from django.core.management import call_command

def main():
    """
    Скрипт для выполнения миграций и создания базы данных
    """
    # Установка переменных окружения Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    
    # Инициализация Django
    django.setup()
    
    # Создание миграций для приложений
    print("Создание миграций...")
    call_command('makemigrations', 'accounts')
    call_command('makemigrations', 'crypto')
    call_command('makemigrations', 'transactions')
    
    # Применение миграций
    print("Применение миграций...")
    call_command('migrate')
    
    # Создание суперпользователя, если его нет
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if not User.objects.filter(is_superuser=True).exists():
        print("Создание суперпользователя...")
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        print("Суперпользователь создан!")
    
    # Создание тестовых данных
    create_test_data()
    
    print("Миграции успешно выполнены!")

def create_test_data():
    """
    Создает тестовые данные для проекта
    """
    from crypto.models import Cryptocurrency, CryptoPrice, ExchangePair
    from decimal import Decimal
    
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
    main() 