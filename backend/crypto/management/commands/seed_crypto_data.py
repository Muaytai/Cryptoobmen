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
                'contract_address': 'TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf', 'decimals': 6  # Nile testnet USDT contract
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
                'name': 'Solana', 'symbol': 'SOL', 'network': 'SOL', 'coingecko_id': 'solana',
                'contract_address': '', 'decimals': 9
            },
            {
                'name': 'Binance Coin', 'symbol': 'BNB', 'network': 'BEP20', 'coingecko_id': 'binancecoin',
                'contract_address': '', 'decimals': 18, 'requires_memo': True
            },

            {'name':'Ripple', 'symbol':'XRP', 'network':'XRP', 
            'coingecko_id':'ripple', 'contract_address':'','decimals':6, 'requires_memo': True
            }
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
            defaults = {
                'name': cur['name'],
                'coingecko_id': cur['coingecko_id'],
                'contract_address': cur['contract_address'],
                'decimals': cur['decimals'],
                'is_active': True,
            }
            # Добавляем requires_memo если указано
            if 'requires_memo' in cur:
                defaults['requires_memo'] = cur['requires_memo']
            
            obj, created = Cryptocurrency.objects.get_or_create(
                symbol=cur['symbol'], network=cur['network'],
                defaults=defaults
            )
            
            # Обновляем requires_memo для существующих валют, если оно указано
            if not created and 'requires_memo' in cur:
                if obj.requires_memo != cur['requires_memo']:
                    obj.requires_memo = cur['requires_memo']
                    obj.save()
                    self.stdout.write(self.style.WARNING(
                        f'Обновлено поле requires_memo для {obj.name} ({obj.symbol} {obj.network}): {cur["requires_memo"]}'
                    ))
            
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
        # НЕ удаляем существующие системные кошельки для валют с memo (XRP, BNB) - они должны быть реальными
        # Удаляем только тестовые адреса для валют без memo
        currencies_with_memo = [c for c in all_currencies if getattr(c, 'requires_memo', False)]
        if currencies_with_memo:
            self.stdout.write(self.style.WARNING(
                f'Пропускаем создание тестовых адресов для валют с memo: {[c.symbol for c in currencies_with_memo]}'
            ))
            self.stdout.write(self.style.WARNING(
                'Используйте команды setup_xrp_system_address или create_system_wallets для настройки реальных адресов'
            ))
        
        # Удаляем только тестовые адреса (которые начинаются с TEST_)
        test_addresses = SystemWalletAddress.objects.filter(address__startswith='TEST_')
        if test_addresses.exists():
            count = test_addresses.count()
            test_addresses.delete()
            self.stdout.write(self.style.WARNING(f'Удалено {count} тестовых системных кошельков.'))

        def generate_test_address(currency_symbol, network_name):
            # Генерируем случайную строку, которая не будет похожа на реальный адрес, чтобы избежать ошибок валидации
            # в tronpy и base58 для тестовых данных.
            unique_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            return f'TEST_{currency_symbol}_{network_name}_{unique_id}'

        # Создаем тестовые адреса только для валют БЕЗ memo
        for cur in all_currencies:
            # Пропускаем валюты с memo - для них нужны реальные адреса
            if getattr(cur, 'requires_memo', False):
                # Проверяем, есть ли уже системный адрес
                existing = SystemWalletAddress.objects.filter(currency=cur).first()
                if existing:
                    self.stdout.write(self.style.SUCCESS(
                        f'Системный кошелек для {cur.symbol} ({cur.network}) уже существует: {existing.address}'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'⚠️  Для {cur.symbol} ({cur.network}) требуется реальный системный адрес! '
                        f'Используйте команду setup_xrp_system_address для XRP или create_system_wallets'
                    ))
                continue
            
            # Для валют без memo создаем тестовые адреса
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