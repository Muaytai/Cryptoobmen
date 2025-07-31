from django.core.management.base import BaseCommand
from crypto.models import UserWallet, Cryptocurrency


class Command(BaseCommand):
    help = 'Проверяет системные кошельки'

    def handle(self, *args, **options):
        self.stdout.write('=== ПРОВЕРКА СИСТЕМНЫХ КОШЕЛЬКОВ ===')
        
        # Проверяем все активные криптовалюты
        currencies = Cryptocurrency.objects.filter(is_active=True)
        
        for currency in currencies:
            self.stdout.write(f'\n--- {currency.symbol} ({currency.network}) ---')
            
            # Ищем системный кошелек для этой валюты
            system_wallet = UserWallet.objects.filter(
                currency=currency,
                is_system_wallet=True,
                is_active=True
            ).first()
            
            if system_wallet:
                self.stdout.write(f'✅ Найден системный кошелек:')
                self.stdout.write(f'   ID: {system_wallet.id}')
                self.stdout.write(f'   Адрес: {system_wallet.deposit_address}')
                self.stdout.write(f'   Баланс: {system_wallet.balance}')
                self.stdout.write(f'   Приватный ключ: {"Есть" if system_wallet.encrypted_private_key else "НЕТ!"}')
                
                if not system_wallet.encrypted_private_key:
                    self.stdout.write(self.style.ERROR('   ⚠️  ОТСУТСТВУЕТ ПРИВАТНЫЙ КЛЮЧ!'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Системный кошелек не найден!'))
        
        # Специально для XRP
        self.stdout.write('\n=== СПЕЦИАЛЬНАЯ ПРОВЕРКА XRP ===')
        xrp_wallets = UserWallet.objects.filter(
            currency__symbol='XRP',
            is_system_wallet=True
        )
        
        self.stdout.write(f'Найдено {xrp_wallets.count()} XRP кошельков:')
        for wallet in xrp_wallets:
            self.stdout.write(f'  ID: {wallet.id}')
            self.stdout.write(f'  Адрес: {wallet.deposit_address}')
            self.stdout.write(f'  Баланс: {wallet.balance}')
            self.stdout.write(f'  Активен: {wallet.is_active}')
            self.stdout.write(f'  Приватный ключ: {"Есть" if wallet.encrypted_private_key else "НЕТ!"}')
            self.stdout.write('  ---') 