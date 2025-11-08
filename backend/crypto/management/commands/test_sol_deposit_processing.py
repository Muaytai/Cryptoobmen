"""
Команда для тестирования обработки депозитов SOL
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import logging

from crypto.models import Cryptocurrency, UserWallet, SystemWalletBalanceLog
from crypto.tasks import check_blockchain_deposits
from crypto.blockchain.factory import get_blockchain_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Тестирует обработку депозитов SOL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID пользователя для тестирования'
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        
        self.stdout.write("=== Тестирование обработки депозитов SOL ===\n")
        
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
            
            # Получаем пользовательские кошельки SOL
            user_wallets = UserWallet.objects.filter(
                currency=sol_currency,
                is_system_wallet=False,
                deposit_address__isnull=False
            ).exclude(deposit_address='')
            
            if not user_wallets.exists():
                self.stdout.write(self.style.WARNING("Пользовательские кошельки SOL не найдены"))
                return
            
            self.stdout.write(f"Найдено {user_wallets.count()} пользовательских кошельков SOL:")
            for wallet in user_wallets:
                self.stdout.write(f"  - Пользователь {wallet.user.id}: {wallet.deposit_address}")
            
            # Проверяем балансы кошельков
            service = get_blockchain_service(sol_currency.network or sol_currency.symbol)
            
            self.stdout.write(f"\n--- Балансы кошельков в блокчейне ---")
            for wallet in user_wallets:
                try:
                    balance = service.get_balance(wallet.deposit_address)
                    self.stdout.write(f"  {wallet.deposit_address}: {balance} SOL")
                except Exception as e:
                    self.stdout.write(f"  {wallet.deposit_address}: Ошибка получения баланса - {e}")
            
            # Запускаем проверку депозитов
            self.stdout.write(f"\n--- Запуск проверки депозитов ---")
            try:
                result = check_blockchain_deposits()
                self.stdout.write(f"Результат: {result}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка при проверке депозитов: {e}"))
                logger.exception("Ошибка при проверке депозитов")
            
            # Проверяем логи системного кошелька
            self.stdout.write(f"\n--- Логи системного кошелька ---")
            recent_logs = SystemWalletBalanceLog.objects.filter(
                currency=sol_currency
            ).order_by('-created_at')[:5]
            
            if recent_logs:
                for log in recent_logs:
                    self.stdout.write(f"  {log.created_at.strftime('%Y-%m-%d %H:%M:%S')} | {log.blockchain_balance} SOL | {log.get_transaction_type_display()}")
            else:
                self.stdout.write("  Логи не найдены")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Общая ошибка: {e}"))
            logger.exception("Общая ошибка при тестировании депозитов SOL")
        
        self.stdout.write("\n=== Тестирование завершено ===")
