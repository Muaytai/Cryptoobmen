from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, UserWallet
from crypto.blockchain.factory import get_blockchain_service
from solders.keypair import Keypair
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Синхронизирует баланс системного кошелька SOL с блокчейном'

    def handle(self, *args, **options):
        self.stdout.write("=== Синхронизация баланса Solana ===\n")
        
        try:
            # Находим SOL валюту
            sol_currency = Cryptocurrency.objects.get(symbol__iexact='SOL', is_active=True)
            
            # Находим системный кошелёк
            system_wallet = UserWallet.objects.get(
                currency=sol_currency,
                is_system_wallet=True,
                is_active=True
            )
            
            self.stdout.write(f"Текущий баланс в БД: {system_wallet.balance} SOL")
            
            if not system_wallet.encrypted_private_key:
                self.stdout.write(self.style.ERROR("✗ Приватный ключ не установлен"))
                return
                
            # Получаем блокчейн сервис
            service = get_blockchain_service(sol_currency.network)
            
            # Получаем адрес кошелька
            key_bytes = service._parse_private_key(system_wallet.encrypted_private_key)
            keypair = Keypair.from_bytes(key_bytes)
            wallet_address = str(keypair.pubkey())
            
            # Получаем баланс из блокчейна
            blockchain_balance = service.get_balance(wallet_address)
            self.stdout.write(f"Баланс в блокчейне: {blockchain_balance} SOL")
            
            if blockchain_balance != system_wallet.balance:
                # Обновляем баланс в базе данных
                old_balance = system_wallet.balance
                system_wallet.balance = blockchain_balance
                system_wallet.available_balance = blockchain_balance - system_wallet.locked_balance
                system_wallet.save()
                
                self.stdout.write(self.style.SUCCESS(
                    f"✓ Баланс синхронизирован: {old_balance} → {blockchain_balance} SOL"
                ))
            else:
                self.stdout.write("✓ Баланс уже синхронизирован")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка: {e}"))
            logger.exception("Ошибка синхронизации баланса")

        self.stdout.write("\n=== Синхронизация завершена ===")