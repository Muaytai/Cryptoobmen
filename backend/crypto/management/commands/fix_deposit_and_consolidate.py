"""
Команда для исправления статуса депозита и запуска консолидации
"""
from django.core.management.base import BaseCommand
from transactions.models import Transaction
from crypto.models import UserWallet, Cryptocurrency
from crypto.blockchain.factory import get_blockchain_service
from decimal import Decimal


class Command(BaseCommand):
    help = 'Исправляет статус депозита и запускает консолидацию'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, default='skrip8078@gmail.com', help='Email пользователя')
        parser.add_argument('--tx-hash', type=str, help='Хеш транзакции депозита')

    def handle(self, *args, **options):
        email = options['email']
        tx_hash = options.get('tx_hash')
        
        # Находим депозит
        if tx_hash:
            deposit = Transaction.objects.filter(tx_hash=tx_hash, user__email=email, type='deposit').first()
        else:
            deposit = Transaction.objects.filter(user__email=email, type='deposit', status='completed').order_by('-timestamp').first()
        
        if not deposit:
            self.stdout.write(self.style.ERROR("Депозит не найден"))
            return
        
        self.stdout.write(f"\n=== Найден депозит ===")
        self.stdout.write(f"TX: {deposit.tx_hash}")
        self.stdout.write(f"Status: {deposit.status}")
        self.stdout.write(f"Amount: {deposit.amount}")
        self.stdout.write(f"Currency: {deposit.crypto.symbol}")
        
        # Проверяем, что это валюта БЕЗ MEMO
        if deposit.crypto.requires_memo:
            self.stdout.write(self.style.WARNING("Это валюта с MEMO, консолидация не требуется"))
            return
        
        # Проверяем баланс на блокчейне
        user_wallet = UserWallet.objects.filter(user=deposit.user, currency=deposit.crypto, is_system_wallet=False).first()
        if not user_wallet or not user_wallet.deposit_address:
            self.stdout.write(self.style.ERROR("Кошелек пользователя не найден или нет адреса"))
            return
        
        self.stdout.write(f"\n=== Проверка баланса на блокчейне ===")
        self.stdout.write(f"User wallet address: {user_wallet.deposit_address}")
        
        try:
            service = get_blockchain_service(deposit.crypto.network or deposit.crypto.symbol)
            blockchain_balance = service.get_balance(user_wallet.deposit_address)
            self.stdout.write(f"Blockchain balance: {blockchain_balance} {deposit.crypto.symbol}")
            
            if blockchain_balance <= 0:
                self.stdout.write(self.style.WARNING("Баланс на блокчейне = 0. Средства уже консолидированы или не поступили."))
                # Проверяем, есть ли консолидация
                consolidation = Transaction.objects.filter(
                    user=deposit.user,
                    crypto=deposit.crypto,
                    type='consolidation',
                    status='completed'
                ).first()
                
                if consolidation:
                    self.stdout.write(f"Найдена завершенная консолидация: {consolidation.tx_hash}")
                    self.stdout.write(self.style.WARNING("Средства должны быть зачислены. Проверьте баланс пользователя."))
                else:
                    self.stdout.write(self.style.ERROR("Консолидация не найдена, но баланс = 0. Возможно, средства не поступили."))
                return
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при проверке баланса: {e}"))
            return
        
        # Если депозит в статусе "completed", меняем на "pending"
        if deposit.status == 'completed':
            self.stdout.write(f"\n=== Исправление статуса депозита ===")
            deposit.status = 'pending'
            deposit.save()
            self.stdout.write(self.style.SUCCESS(f"Статус депозита изменен на 'pending'"))
        
        # Проверяем, есть ли приватный ключ
        if not user_wallet.encrypted_private_key:
            self.stdout.write(self.style.ERROR("У кошелька нет приватного ключа. Консолидация невозможна."))
            return
        
        # Запускаем консолидацию
        self.stdout.write(f"\n=== Запуск консолидации ===")
        from crypto.tasks_consolidation import consolidate_user_deposits
        result = consolidate_user_deposits.delay()
        self.stdout.write(self.style.SUCCESS(f"Задача консолидации запущена: {result.id}"))
        self.stdout.write("Ожидайте подтверждения консолидации (обычно 1-2 минуты)")

