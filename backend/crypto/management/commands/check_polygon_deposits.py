from django.core.management.base import BaseCommand
from crypto.models import UserWallet, Cryptocurrency
from crypto.blockchain.polygon import PolygonService
from transactions.models import Transaction
import logging
import concurrent.futures
from threading import Lock
import time

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Проверить депозиты Polygon для конкретного адреса'

    def add_arguments(self, parser):
        parser.add_argument('--address', type=str, help='Адрес для проверки')
        parser.add_argument('--all-users', action='store_true', help='Проверить всех пользователей')
        parser.add_argument('--blocks-back', type=int, default=50000, help='Количество блоков для проверки назад (по умолчанию 50000)')

    def handle(self, *args, **options):
        service = PolygonService()
        self.stdout.write(f"Подключен к Polygon testnet (Chain ID: {service.w3.eth.chain_id})")
        
        polygon_currency = Cryptocurrency.objects.get(symbol='POL', network='Polygon')
        
        if options['address']:
            # Проверка конкретного адреса
            address = options['address']
            self.check_address(service, address, polygon_currency, options['blocks_back'])
            
        elif options['all_users']:
            # Проверка всех пользователей с Polygon адресами
            user_wallets = UserWallet.objects.filter(
                currency=polygon_currency, 
                is_system_wallet=False, 
                deposit_address__isnull=False
            ).exclude(deposit_address='')
            
            self.stdout.write(f"Найдено {user_wallets.count()} пользователей с Polygon адресами")
            
            for wallet in user_wallets:
                self.stdout.write(f"\nПроверка пользователя {wallet.user_id}: {wallet.deposit_address}")
                self.check_address(service, wallet.deposit_address, polygon_currency, options['blocks_back'], wallet.user)
        else:
            self.stdout.write("Укажите --address или --all-users")

    def check_block_batch(self, service, address, block_numbers, found_transactions, progress_lock, stats):
        """Проверить пакет блоков в отдельном потоке"""
        local_transactions = []
        blocks_processed = 0
        
        for block_num in block_numbers:
            try:
                # Сначала получаем заголовок блока (быстрее)
                block_header = service.w3.eth.get_block(block_num, full_transactions=False)
                
                # Если в блоке нет транзакций, пропускаем
                if not block_header.transactions:
                    blocks_processed += 1
                    continue
                
                # Получаем полный блок только если есть транзакции
                block = service.w3.eth.get_block(block_num, full_transactions=True)
                blocks_processed += 1
                
                # Проверяем транзакции
                for tx in block.transactions:
                    if (tx.to and tx.to.lower() == address.lower() and tx.value > 0):
                        tx_data = {
                            'hash': tx.hash.hex(),
                            'value_wei': tx.value,
                            'value_pol': float(tx.value) / 10**18,
                            'block': block_num,
                            'from': tx['from'],
                            'timestamp': block.timestamp
                        }
                        local_transactions.append(tx_data)
                        
                        # Обновляем общий список с блокировкой
                        with progress_lock:
                            found_transactions.append(tx_data)
                            print(f"\n🎯 Блок {block_num}: найдена TX {tx_data['hash'][:10]}... - {tx_data['value_pol']:.6f} POL")
                
            except Exception as e:
                if not any(keyword in str(e).lower() for keyword in ['extradata', 'poa', 'proof of authority']):
                    print(f"\n⚠ Ошибка блока {block_num}: {str(e)[:50]}...")
                continue
            
            # Небольшая пауза для снижения нагрузки на RPC
            time.sleep(0.01)
        
        # Обновляем статистику
        with progress_lock:
            stats['blocks_processed'] += blocks_processed
            stats['threads_completed'] += 1
            
        return local_transactions

    def check_address(self, service, address, currency, blocks_back, user=None):
        """Проверить конкретный адрес на депозиты"""
        try:
            # Проверим баланс
            balance = service.get_balance(address)
            self.stdout.write(f"Баланс: {balance} POL")
            
            if balance == 0:
                self.stdout.write("Баланс нулевой, пропускаем")
                return
            
            # Проверим транзакции с расширенным диапазоном
            latest_block = service.w3.eth.block_number
            min_block = max(0, latest_block - blocks_back)
            
            # Параллельное сканирование блоков
            self.stdout.write(f"🚀 Запуск параллельного сканирования блоков {min_block} - {latest_block}")
            self.stdout.write(f"📦 Последние {blocks_back} блоков будут проверены в 100 потоков")
            
            # Подготавливаем данные для параллельной обработки
            all_blocks = list(range(latest_block, min_block, -1))[:blocks_back]
            batch_size = max(1, len(all_blocks) // 100)  # Разделяем на 100 пакетов
            
            # Создаем пакеты блоков для каждого потока
            block_batches = []
            for i in range(0, len(all_blocks), batch_size):
                batch = all_blocks[i:i + batch_size]
                if batch:  # Проверяем что пакет не пустой
                    block_batches.append(batch)
            
            self.stdout.write(f"📊 Создано {len(block_batches)} пакетов по ~{batch_size} блоков")
            
            # Инициализируем общие переменные
            found_transactions = []
            progress_lock = Lock()
            stats = {'blocks_processed': 0, 'threads_completed': 0}
            
            start_time = time.time()
            
            # Запускаем параллельную обработку
            with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
                # Создаем отдельный сервис для каждого потока чтобы избежать конфликтов
                futures = []
                
                for i, batch in enumerate(block_batches):
                    # Создаем отдельный сервис для каждого потока
                    thread_service = PolygonService()
                    future = executor.submit(
                        self.check_block_batch, 
                        thread_service, 
                        address, 
                        batch, 
                        found_transactions, 
                        progress_lock, 
                        stats
                    )
                    futures.append(future)
                
                # Мониторим прогресс
                self.stdout.write(f"\n⏳ Ожидаем завершения {len(futures)} потоков...")
                progress_bar_length = 50
                
                while stats['threads_completed'] < len(block_batches):
                    progress = stats['threads_completed'] / len(block_batches)
                    filled_length = int(progress_bar_length * progress)
                    bar = '█' * filled_length + '-' * (progress_bar_length - filled_length)
                    percent = progress * 100
                    elapsed = time.time() - start_time
                    
                    self.stdout.write(f"\r[{bar}] {percent:.1f}% | Потоки: {stats['threads_completed']}/{len(block_batches)} | Блоки: {stats['blocks_processed']} | ТХ: {len(found_transactions)} | {elapsed:.1f}s", ending="")
                    self.stdout.flush()
                    time.sleep(0.5)
                
                # Ждем завершения всех задач
                concurrent.futures.wait(futures)
            
            elapsed_time = time.time() - start_time
            self.stdout.write(f"\r[{'█' * progress_bar_length}] 100.0% | Завершено за {elapsed_time:.1f}s!")
            
            self.stdout.write(f"\n📊 РЕЗУЛЬТАТЫ ПАРАЛЛЕЛЬНОГО СКАНИРОВАНИЯ:")
            self.stdout.write(f"   ⚡ Время выполнения: {elapsed_time:.1f} секунд")
            self.stdout.write(f"   🏃 Потоков использовано: {len(block_batches)}")
            self.stdout.write(f"   📦 Всего найдено транзакций: {len(found_transactions)}")
            self.stdout.write(f"   🔍 Проверено блоков: {stats['blocks_processed']}")
            self.stdout.write(f"   ⚡ Скорость: {stats['blocks_processed'] / elapsed_time:.1f} блоков/сек")
            
            if found_transactions:
                self.stdout.write(f"\n📝 ДЕТАЛИ ТРАНЗАКЦИЙ:")
                for i, tx in enumerate(found_transactions, 1):
                    self.stdout.write(f"   {i}. {tx['hash']} | {tx['value_pol']:.6f} POL | Блок: {tx['block']}")
                    
                    if user:
                        # Добавляем транзакцию в базу если её там нет
                        existing_tx = Transaction.objects.filter(
                            tx_hash=tx['hash'], 
                            user=user
                        ).first()
                        
                        if not existing_tx:
                            self.stdout.write(f"      💾 Добавляем транзакцию в базу...")
                            try:
                                from decimal import Decimal
                                from django.utils import timezone as django_timezone
                                
                                Transaction.objects.create(
                                    user=user,
                                    crypto=currency,
                                    amount=Decimal(str(tx['value_pol'])),
                                    tx_hash=tx['hash'],
                                    type="deposit",
                                    status="completed",
                                    timestamp=django_timezone.fromtimestamp(tx['timestamp'])
                                )
                                
                                # Обновляем баланс пользователя
                                from crypto.models import UserWallet
                                user_wallet = UserWallet.objects.get(user=user, currency=currency)
                                user_wallet.balance += Decimal(str(tx['value_pol']))
                                user_wallet.save()
                                
                                self.stdout.write(f"      ✅ Транзакция добавлена! Баланс обновлен.")
                                
                            except Exception as e:
                                self.stdout.write(f"      ❌ Ошибка добавления: {e}")
            
        except Exception as e:
            self.stdout.write(f"❌ Ошибка проверки адреса {address}: {e}")
