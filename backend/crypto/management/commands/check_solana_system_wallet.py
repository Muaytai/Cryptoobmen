from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, UserWallet
from crypto.blockchain.factory import get_blockchain_service
from decimal import Decimal
from django.db import models
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Проверяет состояние системного кошелька Solana'

    def handle(self, *args, **options):
        self.stdout.write("=== Проверка системного кошелька Solana ===\n")
        
        try:
            # Получаем валюту SOL
            try:
                sol_currency = Cryptocurrency.objects.get(symbol__iexact='SOL', is_active=True)
                self.stdout.write(self.style.SUCCESS(f"✓ Найдена валюта: {sol_currency.name} ({sol_currency.symbol})"))
            except Cryptocurrency.DoesNotExist:
                self.stdout.write(self.style.ERROR("✗ Валюта SOL не найдена в базе данных"))
                return
            
            # Проверяем системный кошелек
            try:
                system_wallet = UserWallet.objects.get(currency=sol_currency, is_system_wallet=True)
                self.stdout.write(self.style.SUCCESS(f"✓ Найден системный кошелек"))
                self.stdout.write(f"  Адрес: {system_wallet.deposit_address}")
                self.stdout.write(f"  Баланс в БД: {system_wallet.balance} SOL")
            except UserWallet.DoesNotExist:
                self.stdout.write(self.style.ERROR("✗ Системный кошелек SOL не найден"))
                return
            
            # Проверяем приватный ключ
            if system_wallet.encrypted_private_key:
                self.stdout.write(self.style.SUCCESS("✓ Приватный ключ установлен"))
            else:
                self.stdout.write(self.style.WARNING("⚠ Приватный ключ отсутствует"))
            
            # Проверяем баланс в блокчейне
            if system_wallet.deposit_address:
                try:
                    service = get_blockchain_service('solana')
                    blockchain_balance = service.get_balance(system_wallet.deposit_address)
                    self.stdout.write(f"  Баланс в блокчейне: {blockchain_balance} SOL")
                    
                    # Сравниваем балансы
                    diff = abs(blockchain_balance - system_wallet.balance)
                    if diff > Decimal('0.000000001'):
                        self.stdout.write(self.style.WARNING(f"⚠ Разница в балансах: {diff} SOL"))
                    else:
                        self.stdout.write(self.style.SUCCESS("✓ Балансы совпадают"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ Ошибка проверки баланса в блокчейне: {e}"))
            
            # Проверяем ожидающие выводы
            try:
                from transactions.models import Transaction
                pending_withdrawals = Transaction.objects.filter(
                    crypto=sol_currency,
                    type='withdrawal',
                    status__in=['pending', 'processing', 'awaiting_confirmation']
                ).count()
                
                self.stdout.write(f"\n--- Ожидающие выводы ---")
                self.stdout.write(f"Количество: {pending_withdrawals}")
                
                if pending_withdrawals > 0:
                    # Подсчитываем общую сумму
                    total_amount = Transaction.objects.filter(
                        crypto=sol_currency,
                        type='withdrawal',
                        status__in=['pending', 'processing', 'awaiting_confirmation']
                    ).aggregate(
                        total=models.Sum('amount')
                    )['total'] or Decimal('0')
                    
                    self.stdout.write(f"Общая сумма: {total_amount} SOL")
                    
                    # Проверяем, достаточно ли средств
                    if system_wallet.balance >= total_amount:
                        self.stdout.write(self.style.SUCCESS("✓ Достаточно средств для выводов"))
                    else:
                        self.stdout.write(self.style.ERROR("✗ Недостаточно средств для выводов"))
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Ошибка проверки ожидающих выводов: {e}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Критическая ошибка: {e}"))
            logger.exception("Критическая ошибка в check_solana_system_wallet")

        self.stdout.write(f"\n=== Проверка завершена ===")