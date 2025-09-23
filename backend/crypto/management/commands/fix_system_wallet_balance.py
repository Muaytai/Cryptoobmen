from django.core.management.base import BaseCommand
from django.conf import settings
from crypto.models import UserWallet, Cryptocurrency
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Исправляет баланс системных кошельков для соответствия с реальностью'

    def add_arguments(self, parser):
        parser.add_argument(
            '--currency',
            type=str,
            default='USDT',
            help='Символ валюты для исправления (по умолчанию USDT)',
        )
        parser.add_argument(
            '--network',
            type=str,
            default='TRC20',
            help='Сеть валюты (по умолчанию TRC20)',
        )
        parser.add_argument(
            '--reset-balance',
            action='store_true',
            help='Сбросить баланс системного кошелька до 0',
        )

    def handle(self, *args, **options):
        currency_symbol = options['currency']
        network = options['network']
        reset_balance = options['reset_balance']
        
        self.stdout.write(f"=== ИСПРАВЛЕНИЕ СИСТЕМНОГО КОШЕЛЬКА {currency_symbol} {network} ===")
        
        try:
            currency = Cryptocurrency.objects.get(symbol=currency_symbol, network=network)
            self.stdout.write(f"✓ Валюта найдена: {currency}")
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"✗ Валюта {currency_symbol} {network} не найдена"))
            return
        
        # Находим системный кошелек
        system_wallets = UserWallet.objects.filter(
            currency=currency,
            is_system_wallet=True
        )
        
        if not system_wallets.exists():
            self.stdout.write(self.style.ERROR(f"✗ Системный кошелек для {currency_symbol} {network} не найден"))
            return
        
        for wallet in system_wallets:
            self.stdout.write(f"\nСистемный кошелек #{wallet.id}:")
            self.stdout.write(f"  Адрес: {wallet.deposit_address}")
            self.stdout.write(f"  Текущий баланс в БД: {wallet.balance}")
            self.stdout.write(f"  Доступный: {wallet.available_balance}")
            self.stdout.write(f"  Заблокирован: {wallet.locked_balance}")
            
            if reset_balance:
                self.stdout.write("\n🔄 Сброс баланса...")
                
                # Сохраняем старые значения для логирования
                old_balance = wallet.balance
                old_available = wallet.available_balance
                old_locked = wallet.locked_balance
                
                # Сбрасываем все балансы
                wallet.balance = Decimal('0.0')
                wallet.available_balance = Decimal('0.0')
                wallet.locked_balance = Decimal('0.0')
                wallet.save()
                
                self.stdout.write(self.style.SUCCESS("✅ Баланс сброшен до 0"))
                self.stdout.write(f"  Было: баланс={old_balance}, доступно={old_available}, заблокировано={old_locked}")
                self.stdout.write(f"  Стало: баланс={wallet.balance}, доступно={wallet.available_balance}, заблокировано={wallet.locked_balance}")
                
                logger.info(f"System wallet {wallet.id} balance reset from {old_balance} to 0")
                
            else:
                self.stdout.write(self.style.WARNING("ℹ️  Для сброса баланса используйте флаг --reset-balance"))
        
        self.stdout.write(f"\n=== РЕКОМЕНДАЦИИ ===")
        self.stdout.write("1. Системный кошелек должен получать USDT только от пользователей через депозиты")
        self.stdout.write("2. Если нужен тестовый USDT, получите его с Nile Faucet:")
        self.stdout.write("   https://nileex.io/join/getJoinPage")
        self.stdout.write("3. После получения USDT, баланс обновится автоматически при следующей консолидации")
        self.stdout.write("4. Или вручную обновите баланс через admin панель")
        
        self.stdout.write(f"\n=== ИСПРАВЛЕНИЕ ЗАВЕРШЕНО ===")
