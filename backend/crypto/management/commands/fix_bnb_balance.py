from django.core.management.base import BaseCommand
from crypto.models import UserWallet, Cryptocurrency
from crypto.blockchain.factory import get_blockchain_service
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Быстрое исправление баланса BNB системного кошелька до реального значения'

    def handle(self, *args, **options):
        self.stdout.write("=== БЫСТРОЕ ИСПРАВЛЕНИЕ БАЛАНСА BNB ===")
        
        try:
            # Получаем валюту BNB BEP20
            currency = Cryptocurrency.objects.get(symbol='BNB', network='BEP20')
            self.stdout.write(f"✓ Валюта найдена: {currency}")
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(self.style.ERROR("✗ Валюта BNB BEP20 не найдена"))
            return
        
        # Находим системный кошелек BNB
        try:
            system_wallet = UserWallet.objects.get(
                currency=currency,
                is_system_wallet=True
            )
            self.stdout.write(f"✓ Системный кошелек найден: ID #{system_wallet.id}")
        except UserWallet.DoesNotExist:
            self.stdout.write(self.style.ERROR("✗ Системный кошелек BNB не найден"))
            return
        
        # Получаем адрес
        address = system_wallet.deposit_address
        if not address:
            self.stdout.write(self.style.ERROR("✗ У системного кошелька не установлен адрес"))
            return
        
        self.stdout.write(f"✓ Адрес: {address}")
        self.stdout.write(f"✓ Текущий баланс в БД: {system_wallet.balance}")
        
        # Получаем реальный баланс из блокчейна
        try:
            service = get_blockchain_service('BEP20')
            real_balance = service.get_balance(address)
            self.stdout.write(f"✓ Реальный баланс: {real_balance} BNB")
            
            # Обновляем баланс
            old_balance = system_wallet.balance
            system_wallet.balance = real_balance
            system_wallet.available_balance = real_balance - system_wallet.locked_balance
            system_wallet.save()
            
            self.stdout.write(self.style.SUCCESS("✅ Баланс исправлен!"))
            self.stdout.write(f"Было: {old_balance}")
            self.stdout.write(f"Стало: {real_balance}")
            
            logger.info(f"BNB system wallet balance fixed from {old_balance} to {real_balance}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Ошибка: {e}"))
            logger.exception("Error fixing BNB balance")
            return
        
        self.stdout.write(f"\n=== ИСПРАВЛЕНИЕ ЗАВЕРШЕНО ===")
