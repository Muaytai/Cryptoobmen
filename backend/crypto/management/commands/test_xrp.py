from django.core.management.base import BaseCommand
from crypto.blockchain.xrp import XRPService
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Тестирует XRP интеграцию'

    def add_arguments(self, parser):
        parser.add_argument(
            '--network',
            type=str,
            default='testnet',
            help='Сеть XRP (testnet или mainnet)'
        )

    def handle(self, *args, **options):
        network = options['network']
        
        self.stdout.write("=== ТЕСТ XRP ИНТЕГРАЦИИ ===")
        self.stdout.write(f"XRP Network: {network}")
        
        try:
            # Инициализируем сервис
            service = XRPService(network=network)
            self.stdout.write(f"✓ XRP сервис инициализирован")
            
            # Проверяем доступность библиотеки
            if not service.client:
                self.stdout.write("✗ XRP клиент недоступен (библиотека xrpl-py не установлена)")
                return
            
            # Тестируем создание адреса
            try:
                address, private_key = service.create_new_address()
                self.stdout.write(f"✓ Создан новый адрес: {address}")
                self.stdout.write(f"  Seed: {private_key[:20]}...")
                
                # Тестируем валидацию адреса
                is_valid = service.validate_address(address)
                self.stdout.write(f"✓ Валидация адреса: {'Валиден' if is_valid else 'Невалиден'}")
                
                # Тестируем получение баланса
                balance = service.get_balance(address)
                self.stdout.write(f"✓ Баланс адреса: {balance} XRP")
                
                # Тестируем получение транзакций
                transactions = service.get_transactions(address)
                self.stdout.write(f"✓ Найдено транзакций: {len(transactions)}")
                
                # Тестируем с известным testnet адресом (если testnet)
                if network == 'testnet':
                    test_address = "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe"  # Известный testnet адрес
                    self.stdout.write(f"\n--- Тестирование с известным адресом: {test_address} ---")
                    
                    test_balance = service.get_balance(test_address)
                    self.stdout.write(f"✓ Баланс тестового адреса: {test_balance} XRP")
                    
                    test_transactions = service.get_transactions(test_address)
                    self.stdout.write(f"✓ Транзакции тестового адреса: {len(test_transactions)}")
                    
                    if test_transactions:
                        for i, tx in enumerate(test_transactions[:3]):  # Показываем первые 3
                            self.stdout.write(f"  TX {i+1}: {tx['transaction_id'][:16]}... Amount: {tx['value']} drops")
                
            except Exception as e:
                self.stdout.write(f"✗ Ошибка при тестировании функций: {e}")
                logger.exception("XRP test error")
                
        except Exception as e:
            self.stdout.write(f"✗ Ошибка при инициализации XRP сервиса: {e}")
            logger.exception("XRP service initialization error")
            
        self.stdout.write("=== ТЕСТ ЗАВЕРШЕН ===")