from django.core.management.base import BaseCommand
from crypto.blockchain.factory import get_blockchain_service
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Тестирует Factory для создания blockchain сервисов'

    def handle(self, *args, **options):
        self.stdout.write("=== ТЕСТ BLOCKCHAIN FACTORY ===")
        
        # Тестируем Bitcoin
        try:
            btc_service = get_blockchain_service('bitcoin')
            self.stdout.write('✓ Bitcoin service создан успешно')
            self.stdout.write(f'  Тип: {type(btc_service).__name__}')
            self.stdout.write(f'  Сеть: {btc_service.network}')
        except Exception as e:
            self.stdout.write(f'✗ Ошибка Bitcoin service: {e}')

        # Тестируем XRP
        try:
            xrp_service = get_blockchain_service('xrp')
            self.stdout.write('✓ XRP service создан успешно')
            self.stdout.write(f'  Тип: {type(xrp_service).__name__}')
            self.stdout.write(f'  Сеть: {xrp_service.network}')
        except Exception as e:
            self.stdout.write(f'✗ Ошибка XRP service: {e}')

        # Тестируем Ethereum
        try:
            eth_service = get_blockchain_service('ethereum')
            self.stdout.write('✓ Ethereum service создан успешно')
            self.stdout.write(f'  Тип: {type(eth_service).__name__}')
            self.stdout.write(f'  Сеть: {eth_service.network}')
        except Exception as e:
            self.stdout.write(f'✗ Ошибка Ethereum service: {e}')

        # Тестируем TRON
        try:
            tron_service = get_blockchain_service('tron')
            self.stdout.write('✓ TRON service создан успешно')
            self.stdout.write(f'  Тип: {type(tron_service).__name__}')
            self.stdout.write(f'  Сеть: {tron_service.network}')
        except Exception as e:
            self.stdout.write(f'✗ Ошибка TRON service: {e}')

        # Тестируем альтернативные названия
        self.stdout.write("\n--- Тестирование альтернативных названий ---")
        
        test_cases = [
            ('btc', 'Bitcoin'),
            ('ripple', 'XRP'),
            ('erc20', 'Ethereum'),
            ('trc20', 'TRON')
        ]
        
        for network_name, description in test_cases:
            try:
                service = get_blockchain_service(network_name)
                self.stdout.write(f'✓ {description} service ({network_name}) создан успешно')
            except Exception as e:
                self.stdout.write(f'✗ Ошибка {description} service ({network_name}): {e}')

        self.stdout.write("=== ТЕСТ ЗАВЕРШЕН ===")