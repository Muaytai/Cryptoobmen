from django.core.management.base import BaseCommand
from crypto.models import SystemWalletAddress, Cryptocurrency
from crypto.blockchain.factory import get_blockchain_service
from decimal import Decimal

class Command(BaseCommand):
    help = 'Тестирует проверку BNB депозитов'

    def handle(self, *args, **options):
        # Адрес для тестирования
        test_address = "0xeA6BFd33720eCEBB96FB7FD1Bf5daCceF890Fa27"
        
        # Получаем BNB валюту
        try:
            bnb_currency = Cryptocurrency.objects.get(symbol='BNB', network='BEP20')
            self.stdout.write(f'Найдена валюта BNB: {bnb_currency.symbol} ({bnb_currency.network})')
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Валюта BNB не найдена. Запустите setup_bnb_system_address.py сначала.')
            )
            return
        
        # Получаем системный адрес
        try:
            system_wallet = SystemWalletAddress.objects.get(currency=bnb_currency, network='BEP20')
            self.stdout.write(f'Найден системный адрес: {system_wallet.address}')
        except SystemWalletAddress.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Системный адрес BNB не найден. Запустите setup_bnb_system_address.py сначала.')
            )
            return
        
        # Тестируем получение транзакций
        try:
            service = get_blockchain_service('BEP20')
            self.stdout.write('Сервис BNB создан успешно')
            
            # Получаем последние транзакции
            transactions = service.get_transactions(address=test_address, min_timestamp=0)
            self.stdout.write(f'Найдено транзакций: {len(transactions)}')
            
            for i, tx in enumerate(transactions[:5]):  # Показываем первые 5
                self.stdout.write(f'Транзакция {i+1}:')
                self.stdout.write(f'  Hash: {tx.get("transaction_id", "N/A")}')
                self.stdout.write(f'  From: {tx.get("from_address", "N/A")}')
                self.stdout.write(f'  To: {tx.get("to_address", "N/A")}')
                self.stdout.write(f'  Value: {tx.get("value", "N/A")}')
                self.stdout.write(f'  Timestamp: {tx.get("timestamp", "N/A")}')
                self.stdout.write('')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при тестировании: {e}')
            )
            return
        
        # Тестируем баланс
        try:
            balance = service.get_balance(test_address)
            self.stdout.write(f'Баланс адреса {test_address}: {balance} BNB')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при получении баланса: {e}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Тестирование завершено!')
        )
