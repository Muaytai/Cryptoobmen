from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, UserWallet
from crypto.blockchain.factory import get_blockchain_service
from crypto.services_deposit import DepositService
from crypto.tasks import check_blockchain_deposits
from accounts.models import User
from transactions.models import Transaction
from decimal import Decimal
import logging
from django.db import transaction

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Исправление проблем с депозитами Solana - комплексный инструмент диагностики и исправления'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix-config',
            action='store_true',
            help='Исправить проблемы конфигурации Solana',
        )
        parser.add_argument(
            '--fix-wallets',
            action='store_true',
            help='Исправить пользовательские кошельки без депозитных адресов',
        )
        parser.add_argument(
            '--test-deposits',
            action='store_true',
            help='Тестировать функциональность сканирования депозитов',
        )
        parser.add_argument(
            '--user-email',
            type=str,
            help='Тестировать депозиты для конкретного пользователя',
        )
        parser.add_argument(
            '--force-scan',
            action='store_true',
            help='Принудительно просканировать все адреса Solana на предмет депозитов',
        )
        parser.add_argument(
            '--fix-all',
            action='store_true',
            help='Запустить все исправления',
        )

    def handle(self, *args, **options):
        self.stdout.write("=== Инструмент исправления депозитов Solana ===\n")
        
        success = True
        
        # Исправить все, если запрошено
        if options.get('fix_all'):
            options['fix_config'] = True
            options['fix_wallets'] = True
            options['test_deposits'] = True
            options['force_scan'] = True
        
        # Шаг 1: Исправить конфигурацию
        if options.get('fix_config', True):
            if not self.fix_solana_configuration():
                success = False
        
        # Шаг 2: Исправить кошельки
        if options.get('fix_wallets') and success:
            if not self.fix_user_wallets():
                success = False
        
        # Шаг 3: Тестировать депозиты
        if options.get('test_deposits') and success:
            self.test_deposit_functionality(options.get('user_email'))
        
        # Шаг 4: Принудительное сканирование
        if options.get('force_scan') and success:
            self.force_scan_deposits()
        
        if success:
            self.stdout.write(self.style.SUCCESS("\n✓ Все исправления выполнены успешно!"))
        else:
            self.stdout.write(self.style.ERROR("\n✗ Некоторые исправления не удались. Проверьте вывод выше."))

    def fix_solana_configuration(self):
        """Исправление конфигурации Solana и подключения к сети"""
        self.stdout.write("\n--- ИСПРАВЛЕНИЕ КОНФИГУРАЦИИ SOLANA ---")
        
        try:
            # 1. Исправить конфигурацию валюты SOL
            try:
                sol_currency = Cryptocurrency.objects.get(symbol__iexact='SOL', is_active=True)
                
                # Исправить поле network, если оно неправильное
                if sol_currency.network != 'solana':
                    old_network = sol_currency.network
                    sol_currency.network = 'solana'
                    sol_currency.save()
                    self.stdout.write(f"✓ Исправлена сеть SOL: {old_network} -> solana")
                
                # Убедиться в правильной конфигурации
                if sol_currency.decimals != 9:
                    sol_currency.decimals = 9
                    sol_currency.save()
                    self.stdout.write(f"✓ Исправлены десятичные знаки SOL: -> 9")
                
                if sol_currency.requires_memo:
                    sol_currency.requires_memo = False
                    sol_currency.save()
                    self.stdout.write(f"✓ Исправлено требование MEMO для SOL: -> False")
                    
                self.stdout.write(f"✓ Валюта SOL настроена: {sol_currency}")
                
            except Cryptocurrency.DoesNotExist:
                self.stdout.write("Создание валюты SOL...")
                sol_currency = Cryptocurrency.objects.create(
                    name='Solana',
                    symbol='SOL',
                    network='solana',
                    decimals=9,
                    is_active=True,
                    requires_memo=False,
                    min_exchange_amount=Decimal('0.01'),
                    fee_percentage=Decimal('0.1')
                )
                self.stdout.write(f"✓ Создана валюта SOL: {sol_currency}")
            
            # 2. Тестировать блокчейн сервис
            try:
                service = get_blockchain_service('solana')
                self.stdout.write(f"✓ Блокчейн сервис инициализирован: {service.__class__.__name__}")
                
                # Тестировать подключение к сети
                test_address = "11111111111111111111111111111112"  # Адрес системной программы
                balance = service.get_balance(test_address)
                self.stdout.write(f"✓ Подключение к сети в порядке")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Ошибка блокчейн сервиса: {e}"))
                return False
            
            # 3. Исправить или создать системный кошелек
            try:
                system_wallet = UserWallet.objects.get(
                    currency=sol_currency,
                    is_system_wallet=True,
                    is_active=True
                )
                self.stdout.write(f"✓ Системный кошелек найден: ID={system_wallet.id}")
                
            except UserWallet.DoesNotExist:
                self.stdout.write("Создание системного кошелька...")
                system_wallet = UserWallet.objects.create(
                    user=None,
                    currency=sol_currency,
                    balance=Decimal('0'),
                    is_system_wallet=True,
                    is_active=True
                )
                self.stdout.write(f"✓ Создан системный кошелек: {system_wallet}")
            
            # 4. Сгенерировать адрес системного кошелька, если отсутствует
            if system_wallet.encrypted_private_key and not system_wallet.deposit_address:
                try:
                    key_bytes = service._parse_private_key(system_wallet.encrypted_private_key)
                    from solders.keypair import Keypair
                    keypair = Keypair.from_bytes(key_bytes)
                    wallet_address = str(keypair.pubkey())
                    system_wallet.deposit_address = wallet_address
                    system_wallet.save()
                    self.stdout.write(f"✓ Сгенерирован адрес системного кошелька: {wallet_address}")
                except Exception as e:
                    self.stdout.write(f"⚠ Не удалось сгенерировать адрес системного кошелька: {e}")
            
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Исправление конфигурации не удалось: {e}"))
            return False

    def fix_user_wallets(self):
        """Исправление пользовательских кошельков без депозитных адресов"""
        self.stdout.write("\n--- ИСПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЬСКИХ КОШЕЛЬКОВ ---")
        
        try:
            sol_currency = Cryptocurrency.objects.get(symbol__iexact='SOL', is_active=True)
            service = get_blockchain_service('solana')
            
            # Найти всех пользователей, которые должны иметь SOL кошельки
            all_users = User.objects.filter(is_active=True)
            
            fixed_count = 0
            created_count = 0
            
            for user in all_users:
                try:
                    # Получить или создать кошелек пользователя
                    wallet, created = UserWallet.objects.get_or_create(
                        user=user,
                        currency=sol_currency,
                        defaults={
                            'balance': Decimal('0'),
                            'is_system_wallet': False,
                            'is_active': True
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(f"✓ Создан кошелек для {user.email}")
                    
                    # Исправить депозитный адрес, если отсутствует
                    if not wallet.deposit_address or wallet.deposit_address == "":
                        new_address, private_key = service.create_new_address(user_id=user.id)
                        wallet.deposit_address = new_address
                        wallet.encrypted_private_key = private_key
                        wallet.save()
                        
                        self.stdout.write(f"✓ Сгенерирован адрес для {user.email}: {new_address}")
                        fixed_count += 1
                        
                except Exception as e:
                    self.stdout.write(f"✗ Не удалось исправить кошелек для {user.email}: {e}")
            
            self.stdout.write(f"✓ Создано {created_count} новых кошельков")
            self.stdout.write(f"✓ Исправлено {fixed_count} адресов кошельков")
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Исправление кошельков не удалось: {e}"))
            return False

    def test_deposit_functionality(self, user_email=None):
        """Тестирование функциональности депозитов для конкретного пользователя"""
        self.stdout.write("\n--- ТЕСТИРОВАНИЕ ФУНКЦИОНАЛЬНОСТИ ДЕПОЗИТОВ ---")
        
        try:
            # Получить тестового пользователя
            if user_email:
                user = User.objects.get(email=user_email)
            else:
                user = User.objects.filter(is_active=True).first()
                
            if not user:
                self.stdout.write(self.style.ERROR("✗ Пользователь для тестирования не найден"))
                return
                
            self.stdout.write(f"Тестирование с пользователем: {user.email}")
            
            # Тестировать генерацию депозитного адреса
            try:
                address, memo, qr_code = DepositService.get_deposit_info(
                    user=user,
                    currency_symbol='SOL',
                    network='solana'
                )
                
                self.stdout.write(f"✓ Депозитный адрес сгенерирован: {address}")
                if memo:
                    self.stdout.write(f"  Memo: {memo}")
                
                # Тестировать подключение к блокчейну для этого адреса
                service = get_blockchain_service('solana')
                balance = service.get_balance(address)
                self.stdout.write(f"  Баланс адреса: {balance} SOL")
                
                # Тестировать сканирование транзакций
                transactions = service.get_transactions(address)
                self.stdout.write(f"  Найдено транзакций: {len(transactions)}")
                
                for tx in transactions[:3]:  # Показать первые 3 транзакции
                    self.stdout.write(f"    TX: {tx.get('transaction_id')} - {tx.get('value')} lamports")
                
                self.stdout.write("✓ Тест функциональности депозитов завершен")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Тест депозитов не удался: {e}"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Настройка теста не удалась: {e}"))

    def force_scan_deposits(self):
        """Принудительное сканирование всех адресов Solana на предмет депозитов"""
        self.stdout.write("\n--- ПРИНУДИТЕЛЬНОЕ СКАНИРОВАНИЕ ДЕПОЗИТОВ ---")
        
        try:
            self.stdout.write("Запуск сканирования депозитов блокчейна...")
            result = check_blockchain_deposits()
            self.stdout.write(f"✓ Сканирование завершено: {result}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Сканирование депозитов не удалось: {e}"))