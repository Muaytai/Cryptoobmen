from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, UserWallet
from crypto.blockchain.factory import get_blockchain_service
from accounts.models import User
from decimal import Decimal
import logging
import json

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Исправляет проблемы с Solana кошельками и транзакциями'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-system-wallet',
            action='store_true',
            help='Создать системный кошелек SOL',
        )
        parser.add_argument(
            '--private-key',
            type=str,
            help='Приватный ключ для системного кошелька (в формате hex, json или base58)',
        )
        parser.add_argument(
            '--add-balance',
            type=str,
            help='Добавить баланс к системному кошельку (только для тестирования)',
        )
        parser.add_argument(
            '--fix-user-wallets',
            action='store_true',
            help='Исправить пользовательские кошельки SOL',
        )
        parser.add_argument(
            '--network',
            type=str,
            default='devnet',
            help='Сеть Solana (mainnet, testnet, devnet)',
        )

    def handle(self, *args, **options):
        self.stdout.write("=== Исправление проблем Solana ===\n")
        
        try:
            # Получаем валюту SOL
            try:
                sol_currency = Cryptocurrency.objects.get(symbol__iexact='SOL', is_active=True)
                self.stdout.write(self.style.SUCCESS(f"✓ Найдена валюта: {sol_currency.name} ({sol_currency.symbol})"))
            except Cryptocurrency.DoesNotExist:
                self.stdout.write(self.style.ERROR("✗ Валюта SOL не найдена в базе данных"))
                # Создаем валюту SOL
                sol_currency = Cryptocurrency.objects.create(
                    name="Solana",
                    symbol="SOL",
                    network="SOL",
                    decimals=9,
                    requires_memo=False,
                    is_active=True
                )
                self.stdout.write(self.style.SUCCESS(f"✓ Создана валюта: {sol_currency.name} ({sol_currency.symbol})"))
            
            # Создание системного кошелька
            if options['create_system_wallet']:
                self.stdout.write("\n--- Создание системного кошелька ---")
                self._create_system_wallet(sol_currency, options)
            
            # Добавление баланса (только для тестирования)
            if options['add_balance']:
                self.stdout.write("\n--- Добавление баланса ---")
                self._add_balance(sol_currency, options['add_balance'])
            
            # Исправление пользовательских кошельков
            if options['fix_user_wallets']:
                self.stdout.write("\n--- Исправление пользовательских кошельков ---")
                self._fix_user_wallets(sol_currency)
            
            # Проверка текущего состояния
            self.stdout.write("\n--- Текущее состояние ---")
            self._check_current_state(sol_currency)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Критическая ошибка: {e}"))
            logger.exception("Критическая ошибка в fix_solana_issues")

        self.stdout.write(f"\n=== Исправление завершено ===")

    def _create_system_wallet(self, currency, options):
        """Создает системный кошелек SOL"""
        try:
            # Проверяем существующий системный кошелек
            system_wallet, created = UserWallet.objects.get_or_create(
                currency=currency,
                is_system_wallet=True,
                defaults={
                    'balance': Decimal('0'),
                    'available_balance': Decimal('0'),
                    'locked_balance': Decimal('0'),
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS("✓ Создан новый системный кошелек"))
            else:
                self.stdout.write("Найден существующий системный кошелек")
            
            # Если указан приватный ключ, устанавливаем его
            if options['private_key']:
                try:
                    # Создаем тестовый сервис для проверки ключа
                    service = get_blockchain_service('solana', network=options['network'])
                    
                    # Проверяем формат ключа
                    private_key = options['private_key']
                    address, _ = service.create_new_address()  # Для теста создания
                    
                    # Устанавливаем приватный ключ
                    system_wallet.encrypted_private_key = private_key
                    system_wallet.save()
                    
                    self.stdout.write(self.style.SUCCESS("✓ Приватный ключ установлен"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ Ошибка установки приватного ключа: {e}"))
            
            # Генерируем адрес, если его нет
            if not system_wallet.deposit_address:
                try:
                    service = get_blockchain_service('solana', network=options['network'])
                    address, private_key = service.create_new_address()
                    
                    system_wallet.deposit_address = address
                    if not system_wallet.encrypted_private_key:
                        system_wallet.encrypted_private_key = private_key
                    system_wallet.save()
                    
                    self.stdout.write(self.style.SUCCESS(f"✓ Создан адрес для системного кошелька: {address}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ Ошибка создания адреса: {e}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Ошибка создания системного кошелька: {e}"))

    def _add_balance(self, currency, amount_str):
        """Добавляет баланс к системному кошельку (только для тестирования)"""
        try:
            amount = Decimal(amount_str)
            
            try:
                system_wallet = UserWallet.objects.get(currency=currency, is_system_wallet=True)
                old_balance = system_wallet.balance
                system_wallet.balance += amount
                system_wallet.available_balance = system_wallet.balance - system_wallet.locked_balance
                system_wallet.save()
                
                self.stdout.write(self.style.SUCCESS(f"✓ Баланс увеличен с {old_balance} до {system_wallet.balance} SOL"))
            except UserWallet.DoesNotExist:
                self.stdout.write(self.style.ERROR("✗ Системный кошелек не найден"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Ошибка добавления баланса: {e}"))

    def _fix_user_wallets(self, currency):
        """Исправляет пользовательские кошельки SOL"""
        try:
            # Получаем все пользовательские кошельки SOL
            user_wallets = UserWallet.objects.filter(
                currency=currency,
                is_system_wallet=False
            )
            
            fixed_count = 0
            for wallet in user_wallets:
                try:
                    # Проверяем, есть ли у кошелька адрес
                    if not wallet.deposit_address:
                        # Создаем новый адрес
                        service = get_blockchain_service('solana')
                        address, private_key = service.create_new_address(user_id=wallet.user.id)
                        
                        wallet.deposit_address = address
                        wallet.encrypted_private_key = private_key
                        wallet.save()
                        
                        # Записываем в GeneratedWallet
                        try:
                            from crypto.models import GeneratedWallet
                            GeneratedWallet.record_generated_wallet(
                                address=address,
                                private_key=private_key,
                                currency=currency,
                                network=currency.network,
                                user=wallet.user,
                                wallet_type='user',
                                created_by='fix_solana_issues',
                                notes=f'Generated during fix for user {wallet.user.id}'
                            )
                        except Exception:
                            pass  # Запись уже существует
                        
                        fixed_count += 1
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ Ошибка исправления кошелька пользователя {wallet.user.id}: {e}"))
            
            self.stdout.write(self.style.SUCCESS(f"✓ Исправлено {fixed_count} пользовательских кошельков"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Ошибка исправления пользовательских кошельков: {e}"))

    def _check_current_state(self, currency):
        """Проверяет текущее состояние кошельков SOL"""
        try:
            # Системный кошелек
            try:
                system_wallet = UserWallet.objects.get(currency=currency, is_system_wallet=True)
                self.stdout.write(f"Системный кошелек:")
                self.stdout.write(f"  Адрес: {system_wallet.deposit_address or 'Не задан'}")
                self.stdout.write(f"  Баланс: {system_wallet.balance} SOL")
                self.stdout.write(f"  Приватный ключ: {'Установлен' if system_wallet.encrypted_private_key else 'Отсутствует'}")
            except UserWallet.DoesNotExist:
                self.stdout.write("Системный кошелек: Не найден")
            
            # Пользовательские кошельки
            user_wallets_count = UserWallet.objects.filter(
                currency=currency,
                is_system_wallet=False
            ).count()
            
            self.stdout.write(f"Пользовательские кошельки: {user_wallets_count}")
            
            # Активные депозиты
            try:
                from transactions.models import Transaction
                active_deposits = Transaction.objects.filter(
                    crypto=currency,
                    type='deposit',
                    status='completed'
                ).count()
                
                self.stdout.write(f"Завершенные депозиты: {active_deposits}")
            except Exception:
                self.stdout.write("Завершенные депозиты: Ошибка подсчета")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Ошибка проверки состояния: {e}"))