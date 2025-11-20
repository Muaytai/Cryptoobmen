"""
Команда для проверки статуса депозита и консолидации
"""
from django.core.management.base import BaseCommand
from transactions.models import Transaction
from crypto.models import UserWallet


class Command(BaseCommand):
    help = 'Проверяет статус депозита и консолидации для пользователя'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, default='skrip8078@gmail.com', help='Email пользователя')

    def handle(self, *args, **options):
        email = options['email']
        
        # Проверяем депозиты
        deposits = Transaction.objects.filter(type='deposit', user__email=email).order_by('-timestamp')
        self.stdout.write(f"\n=== Депозиты для {email} ===")
        for tx in deposits[:5]:
            self.stdout.write(f"TX: {tx.tx_hash}, Status: {tx.status}, Amount: {tx.amount}, Timestamp: {tx.timestamp}")
        
        # Проверяем консолидации
        consolidations = Transaction.objects.filter(type='consolidation', user__email=email).order_by('-timestamp')
        self.stdout.write(f"\n=== Консолидации для {email} ===")
        if consolidations.exists():
            for tx in consolidations[:5]:
                self.stdout.write(f"TX: {tx.tx_hash}, Status: {tx.status}, Amount: {tx.amount}, Timestamp: {tx.timestamp}")
        else:
            self.stdout.write(self.style.WARNING("Нет транзакций консолидации"))
        
        # Проверяем кошельки
        user_wallet = UserWallet.objects.filter(user__email=email, currency__symbol='BTC').first()
        system_wallet = UserWallet.objects.filter(is_system_wallet=True, currency__symbol='BTC').first()
        
        self.stdout.write(f"\n=== Кошельки BTC ===")
        if user_wallet:
            self.stdout.write(f"User wallet address: {user_wallet.deposit_address}")
            self.stdout.write(f"User wallet balance: {user_wallet.balance}")
            self.stdout.write(f"User wallet has private key: {bool(user_wallet.encrypted_private_key)}")
        else:
            self.stdout.write(self.style.ERROR("User wallet not found"))
        
        if system_wallet:
            self.stdout.write(f"System wallet address: {system_wallet.deposit_address}")
            self.stdout.write(f"System wallet balance: {system_wallet.balance}")
            self.stdout.write(f"System wallet has private key: {bool(system_wallet.encrypted_private_key)}")
        else:
            self.stdout.write(self.style.ERROR("System wallet not found"))
        
        if user_wallet and system_wallet:
            addresses_match = user_wallet.deposit_address == system_wallet.deposit_address
            self.stdout.write(f"\n⚠️ Адреса совпадают: {addresses_match}")
            if addresses_match:
                self.stdout.write(self.style.ERROR("❌ ПРОБЛЕМА: У пользовательского и системного кошелька одинаковый адрес!"))
                self.stdout.write(self.style.ERROR("   Это не позволяет консолидации работать правильно."))
                self.stdout.write(self.style.WARNING("\nРешение:"))
                self.stdout.write("1. Убедитесь, что у пользовательского кошелька НЕ стоит галочка 'System Wallet'")
                self.stdout.write("2. Сгенерируйте новый адрес для пользовательского кошелька")
                self.stdout.write("3. Убедитесь, что системный адрес находится в System Wallet Addresses")

