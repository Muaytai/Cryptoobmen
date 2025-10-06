from django.core.management.base import BaseCommand
from crypto.blockchain.solana import SolanaService
from crypto.models import Cryptocurrency, UserWallet
from accounts.models import User
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Тестирует функциональность депозитов Solana'

    def add_arguments(self, parser):
        parser.add_argument(
            '--address',
            type=str,
            help='Адрес для проверки баланса и транзакций',
        )
        parser.add_argument(
            '--network',
            type=str,
            default='devnet',
            help='Сеть Solana (mainnet, testnet, devnet)',
        )

    def handle(self, *args, **options):
        address = options['address']
        network = options['network']
        
        self.stdout.write(f"=== Тест Solana депозитов: сеть {network} ===\n")
        
        try:
            # Создаем сервис Solana
            service = SolanaService(network=network)
            self.stdout.write(self.style.SUCCESS(f"✓ Подключено к Solana {network}"))
            
            # Если адрес не указан, создаем тестовый адрес
            if not address:
                self.stdout.write("Создание тестового адреса...")
                test_address, test_private_key = service.create_new_address()
                self.stdout.write(f"✓ Создан адрес: {test_address}")
                self.stdout.write(f"  Приватный ключ: {test_private_key}")
                address = test_address
            else:
                self.stdout.write(f"Проверка адреса: {address}")
            
            # Проверяем баланс
            self.stdout.write("\n--- Проверка баланса ---")
            try:
                balance = service.get_balance(address)
                self.stdout.write(f"Баланс: {balance} SOL")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка получения баланса: {e}"))
            
            # Проверяем транзакции
            self.stdout.write("\n--- Проверка транзакций ---")
            try:
                transactions = service.get_transactions(address)
                self.stdout.write(f"Найдено транзакций: {len(transactions)}")
                
                for i, tx in enumerate(transactions[:5]):  # Показываем первые 5 транзакций
                    self.stdout.write(f"  {i+1}. {tx['transaction_id'][:20]}... - {tx['value']} SOL")
                    self.stdout.write(f"     От: {tx['from_address'][:20]}...")
                    self.stdout.write(f"     К: {tx['to_address'][:20]}...")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка получения транзакций: {e}"))
            
            # Проверяем валидность адреса
            self.stdout.write("\n--- Проверка валидности адреса ---")
            try:
                is_valid = service.validate_address(address)
                self.stdout.write(f"Адрес {'валиден' if is_valid else 'невалиден'}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка проверки адреса: {e}"))
            
            # Если это тестовый адрес, проверяем работу с приватным ключом
            if not options['address']:
                self.stdout.write("\n--- Тест создания адреса ---")
                try:
                    # Создаем еще один адрес для теста
                    addr1, pk1 = service.create_new_address()
                    addr2, pk2 = service.create_new_address()
                    
                    self.stdout.write(f"Адрес 1: {addr1}")
                    self.stdout.write(f"Адрес 2: {addr2}")
                    
                    # Проверяем, что адреса разные
                    if addr1 != addr2:
                        self.stdout.write(self.style.SUCCESS("✓ Создание адресов работает корректно"))
                    else:
                        self.stdout.write(self.style.ERROR("✗ Создаются одинаковые адреса"))
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Ошибка создания адресов: {e}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Критическая ошибка: {e}"))
            logger.exception("Критическая ошибка в test_solana_deposit")

        self.stdout.write(f"\n=== Тест завершён ===")