from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Тестирует интеграцию Ethereum'

    def handle(self, *args, **options):
        self.stdout.write('=== ТЕСТ ETHEREUM ИНТЕГРАЦИИ ===')
        
        # Проверяем настройки
        self.stdout.write(f'Ethereum Network: {getattr(settings, "ETHEREUM_NETWORK", "Not set")}')
        self.stdout.write(f'Ethereum RPC URL: {getattr(settings, "ETHEREUM_RPC_URL", "Not set")}')
        
        # Проверяем валюты
        try:
            from crypto.models import Cryptocurrency
            eth_currencies = Cryptocurrency.objects.filter(network__iexact='ERC20')
            self.stdout.write(f'\nНайдено {eth_currencies.count()} Ethereum валют:')
            for currency in eth_currencies:
                self.stdout.write(f'  - {currency.name} ({currency.symbol}) - Active: {currency.is_active}')
                if currency.contract_address:
                    self.stdout.write(f'    Contract: {currency.contract_address}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при проверке валют: {e}'))
        
        # Проверяем системные кошельки
        try:
            from crypto.models import UserWallet
            system_wallets = UserWallet.objects.filter(is_system_wallet=True, currency__network__iexact='ERC20')
            self.stdout.write(f'\nСистемные кошельки Ethereum: {system_wallets.count()}')
            for wallet in system_wallets:
                self.stdout.write(f'  - {wallet.currency.symbol}: {wallet.deposit_address or "No address"}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при проверке кошельков: {e}'))
        
        # Тестируем Ethereum сервис
        try:
            from crypto.blockchain.ethereum import EthereumService
            service = EthereumService()
            self.stdout.write(f'\nEthereum сервис создан успешно')
            self.stdout.write(f'Сеть: {service.network}')
            
            # Тестируем создание адреса
            address, private_key = service.create_new_address()
            self.stdout.write(f'Тестовый адрес создан: {address}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при тестировании Ethereum сервиса: {e}'))
        
        self.stdout.write(self.style.SUCCESS('\n=== ТЕСТ ЗАВЕРШЕН ==='))