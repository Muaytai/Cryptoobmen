"""
Команда для проверки баланса кошелька
"""
from django.core.management.base import BaseCommand
from crypto.models import UserWallet
from accounts.models import User


class Command(BaseCommand):
    help = 'Проверяет баланс кошелька пользователя'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, default='skrip8078@gmail.com', help='Email пользователя')
        parser.add_argument('--symbol', type=str, default='BTC', help='Символ валюты')

    def handle(self, *args, **options):
        email = options['email']
        symbol = options['symbol']
        
        try:
            user = User.objects.get(email=email)
            wallet = UserWallet.objects.get(user=user, currency__symbol=symbol, is_active=True)
            
            self.stdout.write(f"\n=== Баланс кошелька {symbol} для {email} ===")
            self.stdout.write(f"Balance: {wallet.balance}")
            self.stdout.write(f"Available Balance: {wallet.available_balance}")
            self.stdout.write(f"Locked Balance: {wallet.locked_balance}")
            self.stdout.write(f"Deposit Address: {wallet.deposit_address}")
            self.stdout.write(f"Is Active: {wallet.is_active}")
            self.stdout.write(f"Is System Wallet: {wallet.is_system_wallet}")
            
            # Проверяем, совпадают ли balance и available_balance
            if wallet.balance != wallet.available_balance:
                self.stdout.write(self.style.WARNING(f"\n⚠️ ВНИМАНИЕ: balance ({wallet.balance}) != available_balance ({wallet.available_balance})"))
                self.stdout.write("Это может быть причиной ошибки при выводе!")
                self.stdout.write("Нужно синхронизировать available_balance с balance.")
            else:
                self.stdout.write(self.style.SUCCESS(f"\n✅ balance и available_balance совпадают"))
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Пользователь {email} не найден"))
        except UserWallet.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Кошелек {symbol} для пользователя {email} не найден"))

