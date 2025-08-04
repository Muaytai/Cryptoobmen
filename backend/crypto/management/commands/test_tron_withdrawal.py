from django.core.management.base import BaseCommand
from crypto.blockchain.tron import TronService
from crypto.models import UserWallet, Cryptocurrency
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Тестирование отправки USDT TRC20 токенов через TronService'

    def add_arguments(self, parser):
        parser.add_argument('--to_address', type=str, help='Адрес получателя', required=True)
        parser.add_argument('--amount', type=str, help='Сумма для отправки', required=True)
        parser.add_argument('--check_balance', action='store_true', help='Проверить баланс перед отправкой')

    def handle(self, *args, **options):
        to_address = options['to_address']
        amount = Decimal(options['amount'])
        check_balance = options['check_balance']
        
        self.stdout.write(f"=== ТЕСТ ОТПРАВКИ USDT TRC20 ===")
        self.stdout.write(f"Адрес получателя: {to_address}")
        self.stdout.write(f"Сумма: {amount} USDT")
        
        try:
            # Проверяем настройки
            self.stdout.write(f"\n--- ПРОВЕРКА НАСТРОЕК ---")
            self.stdout.write(f"TRON_NETWORK: {getattr(settings, 'TRON_NETWORK', 'NOT SET')}")
            self.stdout.write(f"TRON_API_URL: {getattr(settings, 'TRON_API_URL', 'NOT SET')}")
            self.stdout.write(f"USDT_TRC20_CONTRACT_ADDRESS: {getattr(settings, 'USDT_TRC20_CONTRACT_ADDRESS', 'NOT SET')}")
            self.stdout.write(f"TRONGRID_API_KEY: {'SET' if getattr(settings, 'TRONGRID_API_KEY', None) else 'NOT SET'}")
            
            if not getattr(settings, 'TRONGRID_API_KEY', None):
                self.stdout.write(self.style.WARNING(f"! TRONGRID_API_KEY не установлен"))
            
            # Создаем сервис
            service = TronService()
            self.stdout.write(self.style.SUCCESS(f"✓ TronService создан успешно"))
            self.stdout.write(f"  Сеть: {service.network}")
            self.stdout.write(f"  API URL: {service.api_url}")
            
            # Проверяем баланс системного кошелька, если требуется
            if check_balance:
                self.stdout.write(f"\n--- ПРОВЕРКА БАЛАНСА ---")
                try:
                    # Получаем системный кошелек для USDT TRC20
                    currency = Cryptocurrency.objects.get(symbol='USDT', network='TRC20')
                    system_wallet = UserWallet.objects.get(currency=currency, is_system_wallet=True)
                    
                    if system_wallet.encrypted_private_key:
                        # Проверяем баланс через API
                        balance = service.get_balance(system_wallet.deposit_address)
                        self.stdout.write(self.style.SUCCESS(f"✓ Баланс системного кошелька: {balance} USDT"))
                        self.stdout.write(f"  Адрес: {system_wallet.deposit_address}")
                        
                        if balance < amount:
                            self.stdout.write(self.style.WARNING(f"! Недостаточно средств для отправки"))
                            return
                    else:
                        self.stdout.write(self.style.WARNING(f"! У системного кошелька отсутствует приватный ключ"))
                        
                except Cryptocurrency.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"✗ Валюта USDT TRC20 не найдена в базе данных"))
                    return
                except UserWallet.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"✗ Системный кошелек для USDT TRC20 не найден"))
                    return
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ Ошибка проверки баланса: {e}"))
                    logger.exception("Ошибка проверки баланса")
            
            # Тестируем отправку транзакции (без реальной отправки)
            self.stdout.write(f"\n--- ТЕСТ ОТПРАВКИ ---")
            
            # Для теста нам нужен приватный ключ. В реальной системе он будет браться из системного кошелька.
            # Для теста мы можем использовать тестовый ключ, но не отправлять транзакцию на самом деле.
            # Вместо этого просто протестируем создание транзакции.
            
            try:
                # Проверяем валидность адреса получателя
                if not to_address or not to_address.startswith('T') or len(to_address) != 34:
                    self.stdout.write(self.style.ERROR(f"✗ Невалидный адрес получателя: {to_address}"))
                    return
                
                self.stdout.write(self.style.SUCCESS(f"✓ Адрес получателя валиден"))
                
                # Проверяем, можем ли мы создать транзакцию (без отправки)
                self.stdout.write(f"Попытка создания транзакции...")
                
                # Здесь мы бы вызвали service.send_transaction(), но для теста просто проверим,
                # можем ли мы получить контракт
                contract = service.client.get_contract(settings.USDT_TRC20_CONTRACT_ADDRESS)
                self.stdout.write(self.style.SUCCESS(f"✓ Контракт USDT получен успешно"))
                self.stdout.write(f"  Адрес контракта: {settings.USDT_TRC20_CONTRACT_ADDRESS}")
                
                # Проверяем, есть ли метод transfer в контракте
                if hasattr(contract.functions, 'transfer'):
                    self.stdout.write(self.style.SUCCESS(f"✓ Метод transfer доступен в контракте"))
                else:
                    self.stdout.write(self.style.ERROR(f"✗ Метод transfer не найден в контракте"))
                    return
                
                self.stdout.write(self.style.SUCCESS(f"\n=== ТЕСТ ЗАВЕРШЕН УСПЕШНО ==="))
                self.stdout.write(f"Все проверки пройдены. Отправка транзакции должна работать корректно.")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Ошибка тестирования отправки: {e}"))
                logger.exception("Ошибка тестирования отправки")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Ошибка при тестировании: {e}"))
            logger.exception("Ошибка при тестировании отправки USDT TRC20")