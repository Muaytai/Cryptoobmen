from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, ExchangePair, SystemWalletAddress
from decimal import Decimal
import random
import string

class Command(BaseCommand):
    help = 'Автоматически создает основные валюты, пары обмена и системные кошельки для быстрого теста.'

    def handle(self, *args, **options):
        # Валюты и их параметры
        currencies = [
            {
                'name': 'Tether USD', 'symbol': 'USDT', 'network': 'TRC20', 'coingecko_id': 'tether',
                'contract_address': 'TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj', 'decimals': 6
            },
            {
                'name': 'Tether USD', 'symbol': 'USDT', 'network': 'ERC20', 'coingecko_id': 'tether',
                'contract_address': '0xdac17f958d2ee523a2206206994597c13d831ec7', 'decimals': 6
            },
            {
                'name': 'Bitcoin', 'symbol': 'BTC', 'network': 'BTC', 'coingecko_id': 'bitcoin',
                'contract_address': '', 'decimals': 8
            },
            {
                'name': 'Ethereum', 'symbol': 'ETH', 'network': 'ERC20', 'coingecko_id': 'ethereum',
                'contract_address': '', 'decimals': 18
            },
            {
                'name': 'Tron', 'symbol': 'TRX', 'network': 'TRC20', 'coingecko_id': 'tron',
                'contract_address': '', 'decimals': 6
            },
            {
                'name': 'Binance Coin', 'symbol': 'BNB', 'network': 'BEP20', 'coingecko_id': 'binancecoin',
                'contract_address': '', 'decimals': 18
            },
        ]

        # Сначала проверяем существующие валюты и обновляем их поля network, если они null
        existing_currencies = Cryptocurrency.objects.filter(network__isnull=True)
        for currency in existing_currencies:
            matching_cur = next((c for c in currencies if c['symbol'] == currency.symbol), None)
            if matching_cur:
                currency.network = matching_cur['network']
                currency.save()
                self.stdout.write(self.style.WARNING(
                    f'Обновлена существующая валюта {currency.name} ({currency.symbol}): добавлена сеть {currency.network}'
                ))

        # Создаем валюты
        created_currencies = {}
        for cur in currencies:
            obj, created = Cryptocurrency.objects.get_or_create(
                symbol=cur['symbol'], network=cur['network'],
                defaults={
                    'name': cur['name'],
                    'coingecko_id': cur['coingecko_id'],
                    'contract_address': cur['contract_address'],
                    'decimals': cur['decimals'],
                    'is_active': True,
                }
            )
            created_currencies[(cur['symbol'], cur['network'])] = obj
            if created:  # Выводим сообщение только если валюта действительно создана
                self.stdout.write(self.style.SUCCESS(f'Валюта {obj.name} ({obj.symbol} {obj.network}) создана'))
            else:
                self.stdout.write(self.style.WARNING(f'Валюта {obj.name} ({obj.symbol} {obj.network}) уже существует'))

        # Создаем пары обмена (каждая с каждой, кроме одинаковых)
        all_currencies = list(Cryptocurrency.objects.filter(is_active=True))
        for from_cur in all_currencies:
            for to_cur in all_currencies:
                if from_cur == to_cur:
                    continue
                pair, created = ExchangePair.objects.get_or_create(
                    from_crypto=from_cur, to_crypto=to_cur,
                    defaults={
                        'is_active': True,
                        'custom_fee_percentage': Decimal('0.5'),
                    }
                )
                if created: # Выводим сообщение только если пара действительно создана
                    self.stdout.write(self.style.SUCCESS(f'Пара {from_cur.symbol} ({from_cur.network}) → {to_cur.symbol} ({to_cur.network}) создана'))
                else:
                    self.stdout.write(self.style.WARNING(f'Пара {from_cur.symbol} ({from_cur.network}) → {to_cur.symbol} ({to_cur.network}) уже существует'))

        # Создаем тестовые системные кошельки (адреса фейковые)
        # Сначала удаляем все существующие системные кошельки, чтобы избежать дубликатов и устаревших адресов
        SystemWalletAddress.objects.all().delete()
        self.stdout.write(self.style.WARNING('Все существующие системные кошельки удалены.'))

        def generate_test_address(currency_symbol, network_name):
            # Генерируем случайную строку, которая не будет похожа на реальный адрес, чтобы избежать ошибок валидации
            # в tronpy и base58 для тестовых данных.
            unique_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            return f'TEST_{currency_symbol}_{network_name}_{unique_id}'

        for cur in all_currencies:
            addr = generate_test_address(cur.symbol, cur.network)
            obj, created = SystemWalletAddress.objects.get_or_create(
                currency=cur,
                network=cur.network,
                defaults={
                    'address': addr,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Системный кошелек для {cur.symbol} ({cur.network}) создан: {obj.address}'))
            else:
                self.stdout.write(self.style.WARNING(f'Системный кошелек для {cur.symbol} ({cur.network}) уже существует: {obj.address}'))

        self.stdout.write(self.style.SUCCESS('Автозаполнение завершено!')) 