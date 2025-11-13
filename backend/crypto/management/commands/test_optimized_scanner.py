"""
Команда для тестирования оптимизированного сканера блокчейна
"""
import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from crypto.models import Cryptocurrency, UserWallet
from crypto.blockchain.factory import get_blockchain_service
from crypto.optimized_scanner_task import check_blockchain_deposits_optimized, get_scanner_stats


class Command(BaseCommand):
    help = 'Тестирует оптимизированный сканер блокчейна'

    def add_arguments(self, parser):
        parser.add_argument(
            '--currency', 
            type=str, 
            default='POL',
            help='Валюта для тестирования (по умолчанию POL)'
        )
        parser.add_argument(
            '--addresses', 
            type=int, 
            default=5,
            help='Количество адресов для тестирования'
        )
        parser.add_argument(
            '--blocks', 
            type=int, 
            default=100,
            help='Количество блоков для сканирования'
        )
        parser.add_argument(
            '--compare', 
            action='store_true',
            help='Сравнить с обычным сканированием'
        )

    def handle(self, *args, **options):
        currency_symbol = options['currency']
        max_addresses = options['addresses']
        block_count = options['blocks']
        compare_with_normal = options['compare']
        
        self.stdout.write(f"🧪 Тестирование оптимизированного сканера")
        self.stdout.write(f"   Валюта: {currency_symbol}")
        self.stdout.write(f"   Адресов: {max_addresses}")
        self.stdout.write(f"   Блоков: {block_count}")
        
        try:
            # Получаем валюту
            currency = Cryptocurrency.objects.get(symbol=currency_symbol)
            service = get_blockchain_service(currency.network or currency.symbol)
            
            # Проверяем доступность оптимизированного сканера
            if not hasattr(service, 'get_transactions_optimized'):
                self.stdout.write(
                    self.style.ERROR(f"❌ Оптимизированный сканер недоступен для {currency_symbol}")
                )
                return
            
            # Получаем тестовые адреса
            user_wallets = UserWallet.objects.filter(
                currency=currency,
                is_system_wallet=False,
                deposit_address__isnull=False
            ).exclude(deposit_address='')[:max_addresses]
            
            if not user_wallets:
                self.stdout.write(
                    self.style.WARNING("⚠️  Нет пользовательских кошельков для тестирования")
                )
                return
            
            addresses = [wallet.deposit_address for wallet in user_wallets]
            self.stdout.write(f"✅ Найдено {len(addresses)} адресов для тестирования")
            
            # Определяем диапазон блоков
            current_block = service.w3.eth.block_number
            from_block = max(current_block - block_count, 1)
            
            self.stdout.write(f"📊 Диапазон блоков: {from_block} - {current_block}")
            
            # Тест оптимизированного сканирования
            self.stdout.write("\n🚀 Запуск оптимизированного сканирования...")
            start_time = time.time()
            
            try:
                optimized_transactions = service.get_transactions_optimized(
                    addresses=addresses,
                    from_block=from_block,
                    to_block=current_block
                )
                optimized_time = time.time() - start_time
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Оптимизированное сканирование завершено за {optimized_time:.2f}с"
                    )
                )
                self.stdout.write(f"   Найдено транзакций: {len(optimized_transactions)}")
                
                # Показываем статистику сканера
                stats = get_scanner_stats()
                if 'error' not in stats:
                    self.stdout.write("\n📈 Статистика сканера:")
                    for key, value in stats.items():
                        self.stdout.write(f"   {key}: {value}")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Ошибка оптимизированного сканирования: {e}")
                )
                return
            
            # Сравнение с обычным сканированием
            if compare_with_normal:
                self.stdout.write("\n🐌 Запуск обычного сканирования для сравнения...")
                start_time = time.time()
                
                normal_transactions = []
                for address in addresses:
                    try:
                        txs = service.get_transactions(
                            address=address,
                            from_block=from_block,
                            to_block=current_block
                        )
                        normal_transactions.extend(txs)
                    except Exception as e:
                        self.stdout.write(f"   Ошибка для {address}: {e}")
                
                normal_time = time.time() - start_time
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Обычное сканирование завершено за {normal_time:.2f}с"
                    )
                )
                self.stdout.write(f"   Найдено транзакций: {len(normal_transactions)}")
                
                # Сравнение результатов
                speedup = normal_time / optimized_time if optimized_time > 0 else 0
                self.stdout.write(f"\n⚡ Ускорение: {speedup:.1f}x")
                
                if speedup > 1:
                    self.stdout.write(
                        self.style.SUCCESS(f"🎉 Оптимизированное сканирование быстрее!")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING("⚠️  Оптимизация не дала ускорения")
                    )
            
            # Тест полной оптимизированной задачи
            self.stdout.write("\n🔄 Тестирование полной оптимизированной задачи...")
            start_time = time.time()
            
            try:
                result = check_blockchain_deposits_optimized()
                task_time = time.time() - start_time
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Оптимизированная задача завершена за {task_time:.2f}с"
                    )
                )
                self.stdout.write(f"   Результат: {result}")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Ошибка оптимизированной задачи: {e}")
                )
            
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ Валюта {currency_symbol} не найдена")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Общая ошибка: {e}")
            )
