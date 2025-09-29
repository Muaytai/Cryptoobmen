from django.core.management.base import BaseCommand
from crypto.models import UserWallet, Cryptocurrency, SystemWalletAddress
from crypto.blockchain.factory import get_blockchain_service
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Синхронизирует баланс системного кошелька BNB с реальным балансом в блокчейне'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='Обновить баланс в базе данных до реального значения',
        )
        parser.add_argument(
            '--address',
            type=str,
            help='Конкретный адрес для проверки (если не указан, используется адрес из системного кошелька)',
        )

    def handle(self, *args, **options):
        update = options['update']
        specific_address = options['address']
        
        self.stdout.write("=== СИНХРОНИЗАЦИЯ БАЛАНСА BNB КОШЕЛЬКА ===")
        
        try:
            # Получаем валюту BNB BEP20
            currency = Cryptocurrency.objects.get(symbol='BNB', network='BEP20')
            self.stdout.write(f"✓ Валюта найдена: {currency}")
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(self.style.ERROR("✗ Валюта BNB BEP20 не найдена"))
            return
        
        # Определяем адрес для проверки
        check_address = None
        if specific_address:
            check_address = specific_address
            self.stdout.write(f"✓ Используется указанный адрес: {check_address}")
        else:
            # Находим системный кошелек BNB
            try:
                system_wallet = UserWallet.objects.get(
                    currency=currency,
                    is_system_wallet=True
                )
                self.stdout.write(f"✓ Системный кошелек найден: ID #{system_wallet.id}")
                
                # Проверяем адрес в UserWallet
                if system_wallet.deposit_address:
                    check_address = system_wallet.deposit_address
                    self.stdout.write(f"✓ Адрес из UserWallet: {check_address}")
                else:
                    # Ищем адрес в SystemWalletAddress
                    try:
                        system_address = SystemWalletAddress.objects.get(
                            currency=currency,
                            network='BEP20'
                        )
                        check_address = system_address.address
                        self.stdout.write(f"✓ Адрес из SystemWalletAddress: {check_address}")
                    except SystemWalletAddress.DoesNotExist:
                        self.stdout.write(self.style.ERROR("✗ Адрес не найден ни в UserWallet, ни в SystemWalletAddress"))
                        return
                
                # Выводим текущую информацию о кошельке
                self.stdout.write(f"\n--- ТЕКУЩАЯ ИНФОРМАЦИЯ О КОШЕЛЬКЕ ---")
                self.stdout.write(f"Баланс в БД: {system_wallet.balance}")
                self.stdout.write(f"Доступный баланс: {system_wallet.available_balance}")
                self.stdout.write(f"Заблокированный баланс: {system_wallet.locked_balance}")
                
            except UserWallet.DoesNotExist:
                self.stdout.write(self.style.ERROR("✗ Системный кошелек BNB не найден"))
                return
        
        if not check_address:
            self.stdout.write(self.style.ERROR("✗ Адрес для проверки не найден"))
            return
        
        # Получаем реальный баланс из блокчейна
        try:
            service = get_blockchain_service('BEP20')
            self.stdout.write(f"✓ Blockchain service создан: {type(service).__name__}")
            
            real_balance = service.get_balance(check_address)
            self.stdout.write(f"✓ Реальный баланс в блокчейне: {real_balance} BNB")
            self.stdout.write(f"  Адрес: {check_address}")
            
            if not specific_address:
                # Сравниваем балансы только если проверяем системный кошелек
                db_balance = system_wallet.balance
                difference = real_balance - db_balance
                
                self.stdout.write(f"\n--- СРАВНЕНИЕ БАЛАНСОВ ---")
                self.stdout.write(f"Баланс в БД: {db_balance}")
                self.stdout.write(f"Реальный баланс: {real_balance}")
                self.stdout.write(f"Разница: {difference}")
                
                if difference != 0:
                    if difference > 0:
                        self.stdout.write(self.style.WARNING(f"⚠️  Баланс в БД меньше реального на {difference} BNB"))
                    else:
                        self.stdout.write(self.style.WARNING(f"⚠️  Баланс в БД больше реального на {abs(difference)} BNB"))
                    
                    if update:
                        self.stdout.write(f"\n--- ОБНОВЛЕНИЕ БАЛАНСА ---")
                        
                        # Сохраняем старые значения
                        old_balance = system_wallet.balance
                        old_available = system_wallet.available_balance
                        old_locked = system_wallet.locked_balance
                        
                        # Обновляем баланс
                        system_wallet.balance = real_balance
                        system_wallet.available_balance = real_balance - old_locked
                        system_wallet.save()
                        
                        self.stdout.write(self.style.SUCCESS("✅ Баланс обновлен!"))
                        self.stdout.write(f"Было: {old_balance}")
                        self.stdout.write(f"Стало: {real_balance}")
                        self.stdout.write(f"Доступно: {system_wallet.available_balance}")
                        
                        logger.info(f"System wallet BNB balance updated from {old_balance} to {real_balance}")
                    else:
                        self.stdout.write(self.style.WARNING("ℹ️  Для обновления баланса используйте флаг --update"))
                else:
                    self.stdout.write(self.style.SUCCESS("✅ Балансы совпадают!"))
            else:
                self.stdout.write(f"ℹ️  Проверка только реального баланса адреса")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Ошибка получения баланса из блокчейна: {e}"))
            logger.exception("Error getting BNB balance from blockchain")
            return
        
        self.stdout.write(f"\n=== СИНХРОНИЗАЦИЯ ЗАВЕРШЕНА ===")
