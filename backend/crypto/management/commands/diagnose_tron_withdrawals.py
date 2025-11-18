from django.core.management.base import BaseCommand
from django.conf import settings
from crypto.models import UserWallet, Cryptocurrency, SystemWalletAddress
from crypto.blockchain.tron import TronService
from transactions.models import Transaction, Withdrawal
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Диагностирует проблемы с выводом TRON и USDT TRC20'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-system-wallets',
            action='store_true',
            help='Проверить состояние системных кошельков',
        )
        parser.add_argument(
            '--check-failed-withdrawals',
            action='store_true',
            help='Проверить неудачные выводы',
        )
        parser.add_argument(
            '--test-transaction',
            action='store_true',
            help='Протестировать создание транзакции (без отправки)',
        )

    def handle(self, *args, **options):
        self.stdout.write("=== ДИАГНОСТИКА ВЫВОДОВ TRON ===")
        
        # Инициализируем сервис TRON
        try:
            tron_service = TronService('TRC20')
            self.stdout.write("✓ TRON сервис инициализирован")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Ошибка инициализации TRON сервиса: {e}"))
            return

        # Проверяем системные кошельки
        if options['check_system_wallets']:
            self.check_system_wallets(tron_service)

        # Проверяем неудачные выводы
        if options['check_failed_withdrawals']:
            self.check_failed_withdrawals()

        # Тестируем создание транзакции
        if options['test_transaction']:
            self.test_transaction_creation(tron_service)

        if not any([options['check_system_wallets'], options['check_failed_withdrawals'], options['test_transaction']]):
            # Выполняем все проверки, если не указано иное
            self.check_system_wallets(tron_service)
            self.check_failed_withdrawals()
            self.test_transaction_creation(tron_service)

    def check_system_wallets(self, tron_service):
        self.stdout.write("\n=== ПРОВЕРКА СИСТЕМНЫХ КОШЕЛЬКОВ ===")
        
        # Проверяем USDT TRC20 системные кошельки
        try:
            usdt_trc20 = Cryptocurrency.objects.get(symbol='USDT', network='TRC20')
            self.stdout.write(f"✓ USDT TRC20 найден: {usdt_trc20}")
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(self.style.ERROR("✗ USDT TRC20 не найден в БД"))
            return

        # Ищем системные кошельки для USDT TRC20
        system_wallets = UserWallet.objects.filter(
            currency=usdt_trc20,
            is_system_wallet=True
        )
        
        self.stdout.write(f"Найдено системных кошельков: {system_wallets.count()}")
        
        if system_wallets.count() == 0:
            self.stdout.write(self.style.WARNING("⚠️  Нет системных кошельков для USDT TRC20"))
            
            # Проверяем SystemWalletAddress
            system_addresses = SystemWalletAddress.objects.filter(
                currency=usdt_trc20,
                network='TRC20'
            )
            self.stdout.write(f"SystemWalletAddress записей: {system_addresses.count()}")
            
            for addr in system_addresses:
                self.stdout.write(f"  - Адрес: {addr.address}")
                try:
                    balance = tron_service.get_balance(addr.address)
                    self.stdout.write(f"    Баланс: {balance} USDT")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"    Ошибка получения баланса: {e}"))
        else:
            for wallet in system_wallets:
                self.stdout.write(f"\nСистемный кошелек #{wallet.id}:")
                self.stdout.write(f"  - Адрес: {wallet.deposit_address}")
                self.stdout.write(f"  - Баланс в БД: {wallet.balance}")
                self.stdout.write(f"  - Доступный: {wallet.available_balance}")
                self.stdout.write(f"  - Заблокирован: {wallet.locked_balance}")
                self.stdout.write(f"  - Есть приватный ключ: {'Да' if wallet.encrypted_private_key else 'Нет'}")
                
                if wallet.deposit_address:
                    try:
                        # Используем правильный адрес контракта для этой валюты
                        contract_address = usdt_trc20.contract_address
                        self.stdout.write(f"  - Используемый контракт: {contract_address}")
                        real_balance = tron_service.get_balance(wallet.deposit_address, contract_address)
                        self.stdout.write(f"  - Реальный баланс: {real_balance} USDT")
                        
                        if abs(wallet.balance - real_balance) > Decimal('0.000001'):
                            self.stdout.write(self.style.WARNING(
                                f"    ⚠️  Расхождение! БД: {wallet.balance}, Блокчейн: {real_balance}"
                            ))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  - Ошибка проверки баланса: {e}"))
                        
                        # Попробуем с дефолтным контрактом
                        try:
                            self.stdout.write("  - Пробуем с дефолтным контрактом...")
                            default_balance = tron_service.get_balance(wallet.deposit_address)
                            self.stdout.write(f"  - Баланс с дефолтным контрактом: {default_balance} USDT")
                        except Exception as e2:
                            self.stdout.write(self.style.ERROR(f"  - Ошибка с дефолтным контрактом: {e2}"))

    def check_failed_withdrawals(self):
        self.stdout.write("\n=== ПРОВЕРКА НЕУДАЧНЫХ ВЫВОДОВ ===")
        
        # Ищем недавние неудачные выводы USDT TRC20
        failed_withdrawals = Withdrawal.objects.filter(
            transaction__crypto__symbol='USDT',
            transaction__crypto__network='TRC20',
            transaction__status='failed'
        ).order_by('-transaction__timestamp')[:10]
        
        self.stdout.write(f"Найдено неудачных выводов: {failed_withdrawals.count()}")
        
        for withdrawal in failed_withdrawals:
            tx = withdrawal.transaction
            self.stdout.write(f"\nВывод #{withdrawal.id} (Транзакция #{tx.id}):")
            self.stdout.write(f"  - Пользователь: {tx.user.email}")
            self.stdout.write(f"  - Сумма: {tx.amount} USDT")
            self.stdout.write(f"  - Комиссия: {tx.fee} USDT")
            self.stdout.write(f"  - Адрес назначения: {withdrawal.destination_address}")
            self.stdout.write(f"  - Статус: {tx.status}")
            self.stdout.write(f"  - Время: {tx.timestamp}")
            self.stdout.write(f"  - Заметки: {tx.notes}")
            
            if tx.tx_hash:
                self.stdout.write(f"  - TX Hash: {tx.tx_hash}")

    def test_transaction_creation(self, tron_service):
        self.stdout.write("\n=== ТЕСТ СОЗДАНИЯ ТРАНЗАКЦИИ ===")
        
        # Проверяем, есть ли системный кошелек с достаточным балансом
        try:
            usdt_trc20 = Cryptocurrency.objects.get(symbol='USDT', network='TRC20')
            
            system_wallet = UserWallet.objects.filter(
                currency=usdt_trc20,
                is_system_wallet=True,
                balance__gt=0
            ).first()
            
            if not system_wallet:
                self.stdout.write(self.style.WARNING("⚠️  Нет системного кошелька с балансом для теста"))
                return
                
            if not system_wallet.encrypted_private_key:
                self.stdout.write(self.style.ERROR("✗ У системного кошелька нет приватного ключа"))
                return
                
            # Тестовый адрес для отправки (не будем реально отправлять)
            test_address = "TGomTs8vDPfFzeNfzGa4iFFk2hxNeWynHh"  
            test_amount = Decimal('0.1')
            
            self.stdout.write(f"Тестируем отправку {test_amount} USDT на {test_address}")
            self.stdout.write(f"Из системного кошелька: {system_wallet.deposit_address}")
            self.stdout.write(f"Баланс системного кошелька: {system_wallet.balance}")
            
            # Проверяем структуру транзакции без отправки
            try:
                from tronpy.keys import PrivateKey
                from tronpy.contract import Contract
                import json
                
                # Проверяем приватный ключ
                try:
                    priv_key = PrivateKey(bytes.fromhex(system_wallet.encrypted_private_key))
                    from_address = priv_key.public_key.to_base58check_address()
                    self.stdout.write(f"✓ Приватный ключ валиден, адрес: {from_address}")
                    
                    if from_address != system_wallet.deposit_address:
                        self.stdout.write(self.style.ERROR(
                            f"✗ Адрес из ключа ({from_address}) не совпадает с адресом кошелька ({system_wallet.deposit_address})"
                        ))
                        return
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ Ошибка проверки приватного ключа: {e}"))
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
                
                # Проверяем TRX баланс для газа
                try:
                    trx_balance = tron_service.client.get_account_balance(system_wallet.deposit_address)
                    self.stdout.write(f"TRX баланс для газа: {trx_balance} TRX")
                    
                    if trx_balance < 10:  # 10 TRX минимум для газа
                        self.stdout.write(self.style.WARNING(
                            f"⚠️  Низкий баланс TRX для газа: {trx_balance} TRX. Рекомендуется минимум 10 TRX"
                        ))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ Ошибка проверки TRX баланса: {e}"))
                
                self.stdout.write("✓ Все проверки пройдены. Транзакция может быть создана.")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Ошибка при тестировании транзакции: {e}"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Общая ошибка теста: {e}"))

        self.stdout.write("\n=== ДИАГНОСТИКА ЗАВЕРШЕНА ===")
