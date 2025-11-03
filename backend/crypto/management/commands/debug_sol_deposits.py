"""
Команда для детальной диагностики обработки депозитов SOL
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
import logging

from crypto.models import Cryptocurrency, UserWallet
from crypto.blockchain.factory import get_blockchain_service
from crypto.batch_rpc import CachedBatchProcessor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Детальная диагностика обработки депозитов SOL'

    def handle(self, *args, **options):
        self.stdout.write("=== Детальная диагностика обработки депозитов SOL ===\n")
        
        try:
            # Получаем валюту SOL
            sol_currency = Cryptocurrency.objects.filter(
                symbol='SOL',
                is_active=True
            ).first()
            
            if not sol_currency:
                self.stdout.write(self.style.ERROR("Валюта SOL не найдена"))
                return
            
            self.stdout.write(f"Валюта: {sol_currency.name} ({sol_currency.symbol})")
            self.stdout.write(f"Сеть: {sol_currency.network}")
            self.stdout.write(f"Децималы: {sol_currency.decimals}")
            self.stdout.write(f"Требует memo: {sol_currency.requires_memo}")
            
            # Получаем пользовательские кошельки
            user_wallets = UserWallet.objects.filter(
                currency=sol_currency,
                is_system_wallet=False,
                deposit_address__isnull=False
            ).exclude(deposit_address='')
            
            self.stdout.write(f"\nНайдено {user_wallets.count()} пользовательских кошельков:")
            for wallet in user_wallets:
                self.stdout.write(f"  - ID {wallet.id}: Пользователь {wallet.user.id}, адрес {wallet.deposit_address}")
            
            # Получаем сервис
            service = get_blockchain_service(sol_currency.network or sol_currency.symbol)
            
            # Проверяем каждый адрес отдельно
            self.stdout.write(f"\n--- Проверка транзакций по адресам ---")
            for wallet in user_wallets:
                self.stdout.write(f"\nАдрес: {wallet.deposit_address}")
                
                try:
                    # Получаем баланс
                    balance = service.get_balance(wallet.deposit_address)
                    self.stdout.write(f"  Баланс: {balance} SOL")
                    
                    # Получаем транзакции
                    transactions = service.get_transactions(wallet.deposit_address)
                    self.stdout.write(f"  Найдено транзакций: {len(transactions)}")
                    
                    for i, tx in enumerate(transactions, 1):
                        tx_hash = tx.get('transaction_id', 'N/A')
                        value = tx.get('value', '0')
                        amount_sol = Decimal(value) / Decimal(10**9)
                        
                        # Проверяем, есть ли в БД
                        from transactions.models import Transaction
                        existing = Transaction.objects.filter(tx_hash=tx_hash).exists()
                        
                        self.stdout.write(f"    {i}. {tx_hash[:16]}... | {amount_sol} SOL | В БД: {'Да' if existing else 'НЕТ'}")
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Ошибка: {e}"))
            
            # Тестируем батч-обработку
            self.stdout.write(f"\n--- Тестирование батч-обработки ---")
            try:
                batch_results = {}
                addresses = [wallet.deposit_address for wallet in user_wallets]
                
                self.stdout.write(f"Обрабатываем адреса: {addresses}")
                
                # Используем тот же метод, что и в задаче
                cached_batch_processor = CachedBatchProcessor()
                batch_results = cached_batch_processor.process_transactions_batch(
                    addresses, 
                    service, 
                    sol_currency
                )
                
                self.stdout.write(f"Результаты батча:")
                for address, (transactions, success) in batch_results.items():
                    self.stdout.write(f"  {address}: {len(transactions)} транзакций, успех: {success}")
                    
                    if transactions:
                        for tx in transactions:
                            tx_hash = tx.get('transaction_id', 'N/A')
                            value = tx.get('value', '0')
                            amount_sol = Decimal(value) / Decimal(10**9)
                            self.stdout.write(f"    - {tx_hash[:16]}... | {amount_sol} SOL")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка батч-обработки: {e}"))
                logger.exception("Ошибка батч-обработки")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Общая ошибка: {e}"))
            logger.exception("Общая ошибка при диагностике")
        
        self.stdout.write("\n=== Диагностика завершена ===")
