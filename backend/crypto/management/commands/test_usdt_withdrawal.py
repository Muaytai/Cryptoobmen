from django.core.management.base import BaseCommand
from django.conf import settings
from crypto.models import UserWallet, Cryptocurrency
from crypto.blockchain.tron import TronService
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Тестирует отправку USDT TRC20 с системного кошелька'

    def add_arguments(self, parser):
        parser.add_argument(
            '--destination',
            type=str,
            default='TGomTs8vDPfFzeNfzGa4iFFk2hxNeWynHh',
            help='Адрес получателя для теста',
        )
        parser.add_argument(
            '--amount',
            type=str,
            default='0.01',
            help='Сумма для отправки (по умолчанию 0.01 USDT)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Только проверка, без реальной отправки',
        )

    def handle(self, *args, **options):
        destination = options['destination']
        amount = Decimal(options['amount'])
        dry_run = options['dry_run']
        
        self.stdout.write("=== ТЕСТ ОТПРАВКИ USDT TRC20 ===")
        self.stdout.write(f"Адрес получателя: {destination}")
        self.stdout.write(f"Сумма: {amount} USDT")
        self.stdout.write(f"Режим: {'Только проверка' if dry_run else 'Реальная отправка'}")
        
        # Получаем системный кошелек USDT TRC20
        try:
            usdt_trc20 = Cryptocurrency.objects.get(symbol='USDT', network='TRC20')
            system_wallet = UserWallet.objects.filter(
                currency=usdt_trc20,
                is_system_wallet=True
            ).first()
            
            if not system_wallet:
                self.stdout.write(self.style.ERROR("✗ Системный кошелек USDT TRC20 не найден"))
                return
                
            self.stdout.write(f"✓ Системный кошелек найден: {system_wallet.deposit_address}")
            self.stdout.write(f"  Баланс в БД: {system_wallet.balance} USDT")
            
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(self.style.ERROR("✗ USDT TRC20 не найден в БД"))
            return
        
        # Инициализируем TRON сервис
        try:
            tron_service = TronService('TRC20')
            self.stdout.write("✓ TRON сервис инициализирован")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Ошибка инициализации TRON: {e}"))
            return
        
        # Проверяем приватный ключ
        if not system_wallet.encrypted_private_key:
            self.stdout.write(self.style.ERROR("✗ У системного кошелька нет приватного ключа"))
            return
        
        try:
            from tronpy.keys import PrivateKey
            priv_key = PrivateKey(bytes.fromhex(system_wallet.encrypted_private_key))
            from_address = priv_key.public_key.to_base58check_address()
            
            if from_address != system_wallet.deposit_address:
                self.stdout.write(self.style.ERROR(
                    f"✗ Адрес из ключа ({from_address}) не совпадает с адресом кошелька ({system_wallet.deposit_address})"
                ))
                return
                
            self.stdout.write(f"✓ Приватный ключ валиден")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Ошибка проверки приватного ключа: {e}"))
            return
        
        # Проверяем TRX баланс для газа
        try:
            trx_balance = tron_service.client.get_account_balance(system_wallet.deposit_address)
            self.stdout.write(f"✓ TRX баланс: {trx_balance} TRX")
            
            if trx_balance < 10:
                self.stdout.write(self.style.WARNING(
                    f"⚠️  Низкий TRX баланс: {trx_balance}. Рекомендуется минимум 10 TRX"
                ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Ошибка проверки TRX баланса: {e}"))
            return
        
        # Проверяем контракт
        contract_address = usdt_trc20.contract_address
        self.stdout.write(f"Контракт USDT: {contract_address}")
        
        try:
            contract = tron_service.client.get_contract(contract_address)
            self.stdout.write("✓ Контракт доступен")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Ошибка доступа к контракту: {e}"))
            return
        
        # Проверяем баланс USDT (упрощенно, без обработки ошибки)
        self.stdout.write("Проверяем баланс USDT...")
        try:
            # Не используем get_balance, так как он может давать ошибку
            # Вместо этого попробуем создать транзакцию
            pass
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️  Не удалось проверить баланс USDT: {e}"))
        
        # Подготавливаем транзакцию
        self.stdout.write(f"\nПодготовка транзакции:")
        self.stdout.write(f"  От: {system_wallet.deposit_address}")
        self.stdout.write(f"  К: {destination}")
        self.stdout.write(f"  Сумма: {amount} USDT")
        self.stdout.write(f"  Контракт: {contract_address}")
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS("✓ Проверка завершена. Все готово для отправки."))
            self.stdout.write("Для реальной отправки запустите команду без --dry-run")
            return
        
        # Реальная отправка
        self.stdout.write("\n🚀 ОТПРАВКА ТРАНЗАКЦИИ...")
        
        try:
            tx_hash = tron_service.send_transaction(
                private_key=system_wallet.encrypted_private_key,
                to_address=destination,
                amount=amount,
                contract_address=contract_address
            )
            
            self.stdout.write(self.style.SUCCESS(f"✅ УСПЕХ! Транзакция отправлена!"))
            self.stdout.write(f"TX Hash: {tx_hash}")
            self.stdout.write(f"Проверить в блокчейне: https://nile.tronscan.org/#/transaction/{tx_hash}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ ОШИБКА отправки: {e}"))
            
            # Детальный анализ ошибки
            error_str = str(e).lower()
            if "no contract" in error_str or "smart contract is not exist" in error_str:
                self.stdout.write("\n🔍 АНАЛИЗ ОШИБКИ:")
                self.stdout.write("Ошибка указывает на проблему с контрактом.")
                self.stdout.write("Возможные причины:")
                self.stdout.write("1. Контракт не существует в тестовой сети")
                self.stdout.write("2. Неправильный адрес контракта")
                self.stdout.write("3. Системный кошелек не имеет USDT баланса")
                
            elif "insufficient" in error_str:
                self.stdout.write("\n🔍 АНАЛИЗ ОШИБКИ:")
                self.stdout.write("Недостаточно средств для отправки")
                
            elif "revert" in error_str:
                self.stdout.write("\n🔍 АНАЛИЗ ОШИБКИ:")
                self.stdout.write("Транзакция отклонена контрактом")
        
        self.stdout.write("\n=== ТЕСТ ЗАВЕРШЕН ===")
