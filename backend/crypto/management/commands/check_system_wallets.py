from django.core.management.base import BaseCommand
from crypto.models import UserWallet, Cryptocurrency
from crypto.blockchain.factory import get_blockchain_service
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Проверка системных кошельков'

    def handle(self, *args, **options):
        self.stdout.write("=== ПРОВЕРКА СИСТЕМНЫХ КОШЕЛЬКОВ ===")
        
        # Получаем все активные криптовалюты
        cryptocurrencies = Cryptocurrency.objects.filter(is_active=True, currency_type='crypto')
        
        if not cryptocurrencies.exists():
            self.stdout.write(self.style.WARNING("Нет активных криптовалют в базе данных"))
            return
        
        self.stdout.write(f"Найдено {cryptocurrencies.count()} активных криптовалют")
        
        for currency in cryptocurrencies:
            self.stdout.write(f"\n--- {currency.name} ({currency.symbol} - {currency.network}) ---")
            
            # Проверяем системный кошелек
            try:
                system_wallet = UserWallet.objects.get(
                    currency=currency,
                    is_system_wallet=True
                )
                self.stdout.write(self.style.SUCCESS(f"✓ Системный кошелек существует"))
                self.stdout.write(f"  Баланс: {system_wallet.balance}")
                self.stdout.write(f"  Доступный баланс: {system_wallet.available_balance}")
                self.stdout.write(f"  Заблокированный баланс: {system_wallet.locked_balance}")
                self.stdout.write(f"  Активен: {system_wallet.is_active}")
                
                if system_wallet.deposit_address:
                    self.stdout.write(f"  Адрес: {system_wallet.deposit_address}")
                else:
                    self.stdout.write(self.style.WARNING(f"! Адрес не установлен"))
                
                if system_wallet.encrypted_private_key:
                    self.stdout.write(self.style.SUCCESS(f"✓ Приватный ключ установлен"))
                else:
                    self.stdout.write(self.style.WARNING(f"! Приватный ключ не установлен"))
                    
                # Для USDT TRC20 проверяем дополнительные параметры
                if currency.symbol == 'USDT' and currency.network == 'TRC20':
                    self.stdout.write(f"\n  [TRC20] Проверка настроек:")
                    self.stdout.write(f"    USDT_TRC20_CONTRACT_ADDRESS: {getattr(settings, 'USDT_TRC20_CONTRACT_ADDRESS', 'NOT SET')}")
                    self.stdout.write(f"    TRON_NETWORK: {getattr(settings, 'TRON_NETWORK', 'NOT SET')}")
                    self.stdout.write(f"    TRON_API_URL: {getattr(settings, 'TRON_API_URL', 'NOT SET')}")
                    
                    # Проверяем, можем ли создать сервис
                    try:
                        service = get_blockchain_service(currency.network)
                        self.stdout.write(self.style.SUCCESS(f"    ✓ Blockchain service создан"))
                        self.stdout.write(f"      Тип: {type(service).__name__}")
                        self.stdout.write(f"      Сеть: {service.network}")
                        
                        # Проверяем баланс, если есть адрес и приватный ключ
                        if system_wallet.deposit_address and system_wallet.encrypted_private_key:
                            try:
                                balance = service.get_balance(system_wallet.deposit_address)
                                self.stdout.write(self.style.SUCCESS(f"    ✓ Баланс проверен: {balance} USDT"))
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(f"    ! Ошибка проверки баланса: {e}"))
                                
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"    ✗ Ошибка создания blockchain service: {e}"))
                        
            except UserWallet.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"! Системный кошелек не найден"))
                self.stdout.write(f"  Создайте его с помощью команды: python manage.py create_system_wallets")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Ошибка проверки кошелька: {e}"))
                logger.exception(f"Ошибка проверки кошелька для {currency.symbol}")
        
        self.stdout.write(self.style.SUCCESS(f"\n=== ПРОВЕРКА ЗАВЕРШЕНА ==="))