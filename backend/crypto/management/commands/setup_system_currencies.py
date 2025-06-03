from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, SystemWallet
from django.db import transaction
from decimal import Decimal

class Command(BaseCommand):
    help = 'Создает системные валюты и кошельки для них'

    def handle(self, *args, **options):
        # Список системных валют для создания
        system_currencies = [
            {
                'name': 'Российский рубль',
                'symbol': 'RUB',
                'is_system': True,
                'is_active': True,
                'fee_percentage': Decimal('0.5'),
                'min_amount': Decimal('100'),
                'max_amount': Decimal('100000'),
            },
            {
                'name': 'Доллар США',
                'symbol': 'USD',
                'is_system': True,
                'is_active': True,
                'fee_percentage': Decimal('0.5'),
                'min_amount': Decimal('1'),
                'max_amount': Decimal('10000'),
            },
            {
                'name': 'Евро',
                'symbol': 'EUR',
                'is_system': True,
                'is_active': True,
                'fee_percentage': Decimal('0.5'),
                'min_amount': Decimal('1'),
                'max_amount': Decimal('10000'),
            },
        ]

        # Список криптовалют для создания
        crypto_currencies = [
            {
                'name': 'Bitcoin',
                'symbol': 'BTC',
                'is_system': False,
                'is_active': True,
                'fee_percentage': Decimal('0.2'),
                'min_amount': Decimal('0.0001'),
                'max_amount': Decimal('10'),
                'coingecko_id': 'bitcoin',
            },
            {
                'name': 'Ethereum',
                'symbol': 'ETH',
                'is_system': False,
                'is_active': True,
                'fee_percentage': Decimal('0.2'),
                'min_amount': Decimal('0.001'),
                'max_amount': Decimal('100'),
                'coingecko_id': 'ethereum',
            },
            {
                'name': 'Tether',
                'symbol': 'USDT',
                'is_system': False,
                'is_active': True,
                'fee_percentage': Decimal('0.1'),
                'min_amount': Decimal('1'),
                'max_amount': Decimal('100000'),
                'coingecko_id': 'tether',
            },
        ]

        with transaction.atomic():
            # Создаем системные валюты
            for currency_data in system_currencies:
                currency, created = Cryptocurrency.objects.get_or_create(
                    symbol=currency_data['symbol'],
                    defaults=currency_data
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Создана системная валюта: {currency.name} ({currency.symbol})'))
                else:
                    # Обновляем существующую валюту
                    for key, value in currency_data.items():
                        setattr(currency, key, value)
                    currency.save()
                    self.stdout.write(self.style.WARNING(f'Обновлена системная валюта: {currency.name} ({currency.symbol})'))
                
                # Создаем системный кошелек для валюты
                system_wallet, wallet_created = SystemWallet.objects.get_or_create(
                    crypto=currency,
                    defaults={
                        'balance': Decimal('1000000'),  # Начальный баланс системного кошелька
                        'available_balance': Decimal('1000000'),
                    }
                )
                
                if wallet_created:
                    self.stdout.write(self.style.SUCCESS(f'Создан системный кошелек для {currency.symbol}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Системный кошелек для {currency.symbol} уже существует'))
            
            # Создаем криптовалюты
            for currency_data in crypto_currencies:
                currency, created = Cryptocurrency.objects.get_or_create(
                    symbol=currency_data['symbol'],
                    defaults=currency_data
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Создана криптовалюта: {currency.name} ({currency.symbol})'))
                else:
                    # Обновляем существующую валюту
                    for key, value in currency_data.items():
                        setattr(currency, key, value)
                    currency.save()
                    self.stdout.write(self.style.WARNING(f'Обновлена криптовалюта: {currency.name} ({currency.symbol})'))
