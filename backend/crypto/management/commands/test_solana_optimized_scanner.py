from django.core.management.base import BaseCommand
from crypto.blockchain.solana import SolanaService
from decimal import Decimal
import logging
import time

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Тестирует оптимизированный сканер Solana'

    def add_arguments(self, parser):
        parser.add_argument(
            '--addresses',
            type=str,
            nargs='+',
            help='Адреса для сканирования (по умолчанию будут созданы тестовые адреса)',
        )
        parser.add_argument(
            '--network',
            type=str,
            default='devnet',
            help='Сеть Solana (mainnet, testnet, devnet)',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=3,
            help='Количество тестовых адресов для создания (если не указаны конкретные адреса)',
        )

    def handle(self, *args, **options):
        addresses = options['addresses']
        network = options['network']
        count = options['count']
        
        self.stdout.write(f"=== Тест оптимизированного сканера Solana: сеть {network} ===\n")
        
        try:
            # Создаем сервис Solana
            service = SolanaService(network=network)
            self.stdout.write(self.style.SUCCESS(f"✓ Подключено к Solana {network}"))
            
            # Если адреса не указаны, создаем тестовые адреса
            if not addresses:
                self.stdout.write(f"Создание {count} тестовых адресов...")
                addresses = []
                for i in range(count):
                    test_address, test_private_key = service.create_new_address()
                    addresses.append(test_address)
                    self.stdout.write(f"  {i+1}. {test_address}")
            else:
                self.stdout.write(f"Сканирование {len(addresses)} адресов...")
                for i, addr in enumerate(addresses):
                    self.stdout.write(f"  {i+1}. {addr}")
            
            # Тестируем обычное сканирование
            self.stdout.write("\n--- Тест обычного сканирования ---")
            start_time = time.time()
            total_transactions = 0
            
            for address in addresses[:3]:  # Ограничиваем для теста
                try:
                    transactions = service.get_transactions(address)
                    count = len(transactions)
                    total_transactions += count
                    self.stdout.write(f"  {address[:20]}...: {count} транзакций")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Ошибка сканирования {address[:20]}...: {e}"))
            
            regular_time = time.time() - start_time
            self.stdout.write(f"Обычное сканирование: {total_transactions} транзакций за {regular_time:.2f} секунд")
            
            # Тестируем оптимизированное сканирование
            self.stdout.write("\n--- Тест оптимизированного сканирования ---")
            start_time = time.time()
            
            try:
                optimized_transactions = service.get_transactions_optimized(addresses)
                optimized_time = time.time() - start_time
                self.stdout.write(self.style.SUCCESS(f"✓ Оптимизированное сканирование: {len(optimized_transactions)} транзакций за {optimized_time:.2f} секунд"))
                
                # Сравнение производительности
                if regular_time > 0:
                    speedup = regular_time / optimized_time if optimized_time > 0 else float('inf')
                    self.stdout.write(f"  Ускорение: {speedup:.2f}x")
                
                # Показываем статистику оптимизированного сканера
                if hasattr(service, 'optimized_scanner') and service.optimized_scanner:
                    stats = service.optimized_scanner.get_stats()
                    self.stdout.write(f"  Статистика сканера:")
                    self.stdout.write(f"    Адресов просканировано: {stats.get('addresses_scanned', 0)}")
                    self.stdout.write(f"    Транзакций найдено: {stats.get('transactions_found', 0)}")
                    self.stdout.write(f"    Попаданий в кэш: {stats.get('cache_hits', 0)}")
                    self.stdout.write(f"    Промахов кэша: {stats.get('cache_misses', 0)}")
                    self.stdout.write(f"    Ошибок: {stats.get('errors', 0)}")
                    self.stdout.write(f"    Общее время: {stats.get('total_time', 0):.2f} секунд")
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка оптимизированного сканирования: {e}"))
                logger.exception("Ошибка оптимизированного сканирования")
            
            # Тестируем работу с кэшем
            self.stdout.write("\n--- Тест кэширования ---")
            try:
                # Повторное сканирование тех же адресов
                start_time = time.time()
                cached_transactions = service.get_transactions_optimized(addresses)
                cache_time = time.time() - start_time
                self.stdout.write(self.style.SUCCESS(f"✓ Повторное сканирование: {len(cached_transactions)} транзакций за {cache_time:.2f} секунд"))
                
                if optimized_time > 0:
                    cache_speedup = optimized_time / cache_time if cache_time > 0 else float('inf')
                    self.stdout.write(f"  Ускорение за счет кэша: {cache_speedup:.2f}x")
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка тестирования кэша: {e}"))
                logger.exception("Ошибка тестирования кэша")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Критическая ошибка: {e}"))
            logger.exception("Критическая ошибка в test_solana_optimized_scanner")

        self.stdout.write(f"\n=== Тест завершён ===")