"""
Команда для проверки транзакций на конкретном адресе SOL
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
import logging

from crypto.blockchain.factory import get_blockchain_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Проверяет транзакции на конкретном адресе SOL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--address',
            type=str,
            required=True,
            help='Адрес для проверки транзакций'
        )
        parser.add_argument(
            '--network',
            type=str,
            default='SOL',
            help='Сеть (по умолчанию SOL)'
        )

    def handle(self, *args, **options):
        address = options['address']
        network = options['network']
        
        self.stdout.write(f"=== Проверка транзакций на адресе {address} ===\n")
        
        try:
            # Получаем сервис блокчейна
            service = get_blockchain_service(network)
            
            # Получаем баланс
            balance = service.get_balance(address)
            self.stdout.write(f"Баланс: {balance} SOL")
            
            # Получаем транзакции
            self.stdout.write(f"\n--- Транзакции ---")
            transactions = service.get_transactions(address)
            
            if not transactions:
                self.stdout.write("Транзакции не найдены")
                return
            
            self.stdout.write(f"Найдено {len(transactions)} транзакций:")
            
            for i, tx in enumerate(transactions, 1):
                tx_hash = tx.get('transaction_id', 'N/A')
                value = tx.get('value', '0')
                from_addr = tx.get('from_address', 'N/A')
                to_addr = tx.get('to_address', 'N/A')
                
                # Конвертируем lamports в SOL
                try:
                    amount_sol = Decimal(value) / Decimal(10**9)  # 9 decimals для SOL
                except:
                    amount_sol = Decimal('0')
                
                self.stdout.write(f"\n{i}. Транзакция: {tx_hash}")
                self.stdout.write(f"   От: {from_addr}")
                self.stdout.write(f"   К: {to_addr}")
                self.stdout.write(f"   Сумма: {amount_sol} SOL ({value} lamports)")
                
                # Проверяем, есть ли эта транзакция в БД
                from transactions.models import Transaction
                existing_tx = Transaction.objects.filter(tx_hash=tx_hash).first()
                if existing_tx:
                    self.stdout.write(f"   ✅ Найдена в БД: пользователь {existing_tx.user.id}, сумма {existing_tx.amount}")
                else:
                    self.stdout.write(f"   ❌ НЕ найдена в БД")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка: {e}"))
            logger.exception("Ошибка при проверке транзакций")
        
        self.stdout.write("\n=== Проверка завершена ===")
