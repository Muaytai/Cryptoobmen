from django.core.management.base import BaseCommand
from crypto.blockchain.bitcoin import BitcoinService
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Тестирует Bitcoin интеграцию'

    def add_arguments(self, parser):
        parser.add_argument(
            '--network',
            type=str,
            default='testnet',
            help='Сеть Bitcoin (testnet или mainnet)'
        )

    def handle(self, *args, **options):
        network = options['network']
        
        self.stdout.write("=== ТЕСТ BITCOIN ИНТЕГРАЦИИ ===")
        self.stdout.write(f"Bitcoin Network: {network}")
        
        try:
            # Инициализируем сервис
            service = BitcoinService(network=network)
            self.stdout.write(f"✓ Bitcoin сервис инициализирован")
            
            # Тестируем создание адреса
            try:
                address, private_key = service.create_new_address()
                self.stdout.write(f"✓ Создан новый адрес: {address}")
                self.stdout.write(f"  Приватный ключ: {private_key[:10]}...")
                
                # Тестируем валидацию адреса
                is_valid = service.validate_address(address)
                self.stdout.write(f"✓ Валидация адреса: {'Валиден' if is_valid else 'Невалиден'}")
                
                # Тестируем получение баланса
                balance = service.get_balance(address)
                self.stdout.write(f"✓ Баланс адреса: {balance} BTC")
                
                # Тестируем получение транзакций
                transactions = service.get_transactions(address)
                self.stdout.write(f"✓ Найдено транзакций: {len(transactions)}")
                
            except Exception as e:
                self.stdout.write(f"✗ Ошибка при тестировании функций: {e}")
                
        except Exception as e:
            self.stdout.write(f"✗ Ошибка при инициализации Bitcoin сервиса: {e}")
            
        self.stdout.write("=== ТЕСТ ЗАВЕРШЕН ===")