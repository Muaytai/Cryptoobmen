from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, UserWallet
from crypto.blockchain.factory import get_blockchain_service
from transactions.models import Transaction
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Проверяет и исправляет состояние Solana кошельков'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix-addresses',
            action='store_true',
            help='Создать отсутствующие адреса для кошельков',
        )
        parser.add_argument(
            '--sync-balances',
            action='store_true',
            help='Синхронизировать балансы с блокчейном',
        )
        parser.add_argument(
            '--check-transactions',
            action='store_true',
            help='Проверить последние транзакции в блокчейне',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Проверить только конкретного пользователя',
        )

    def handle(self, *args, **options):
        self.stdout.write("=== Диагностика Solana кошельков ===\n")
        
        try:
            # Находим Solana валюту
            sol_currency = Cryptocurrency.objects.get(symbol__iexact='SOL', is_active=True)
            self.stdout.write(f"✓ Валюта: {sol_currency.name} ({sol_currency.symbol})")
            self.stdout.write(f"  Сеть: {sol_currency.network}")
            self.stdout.write(f"  Требует MEMO: {sol_currency.requires_memo}")
            self.stdout.write(f"  Активна: {sol_currency.is_active}")
            
            # Получаем блокчейн сервис
            service = get_blockchain_service(sol_currency.network or sol_currency.symbol)
            self.stdout.write(f"✓ Блокчейн сервис: {service.__class__.__name__}")
            
            # Проверяем системный кошелек
            self.stdout.write(f"\n--- СИСТЕМНЫЙ КОШЕЛЕК ---")
            try:
                system_wallet = UserWallet.objects.get(
                    currency=sol_currency,
                    is_system_wallet=True,
                    is_active=True
                )
                self.stdout.write(f"✓ Найден: ID={system_wallet.id}")
                self.stdout.write(f"  Баланс в БД: {system_wallet.balance} SOL")
                self.stdout.write(f"  Доступный: {system_wallet.available_balance} SOL")
                self.stdout.write(f"  Заблокированный: {system_wallet.locked_balance} SOL")
                
                if system_wallet.deposit_address:
                    self.stdout.write(f"  Адрес: {system_wallet.deposit_address}")
                    
                    if options.get('sync_balances') or options.get('check_transactions'):
                        try:
                            blockchain_balance = service.get_balance(system_wallet.deposit_address)
                            self.stdout.write(f"  Баланс в блокчейне: {blockchain_balance} SOL")
                            
                            diff = blockchain_balance - system_wallet.balance
                            if abs(diff) > Decimal('0.001'):  # Допустимая погрешность
                                self.stdout.write(f"  ⚠ Расхождение: {diff:+.6f} SOL")
                            else:
                                self.stdout.write(f"  ✅ Балансы синхронизированы")
                                
                        except Exception as e:
                            self.stdout.write(f"  ✗ Ошибка проверки баланса: {e}")
                else:
                    self.stdout.write(f"  ⚠ Адрес отсутствует")
                    
                if not system_wallet.encrypted_private_key:
                    self.stdout.write(f"  ⚠ Приватный ключ отсутствует")
                else:
                    self.stdout.write(f"  ✓ Приватный ключ установлен")
                    
            except UserWallet.DoesNotExist:
                self.stdout.write(self.style.ERROR("✗ Системный кошелек не найден!"))
            
            # Проверяем пользовательские кошельки
            self.stdout.write(f"\n--- ПОЛЬЗОВАТЕЛЬСКИЕ КОШЕЛЬКИ ---")
            
            wallets_query = UserWallet.objects.filter(
                currency=sol_currency,
                is_system_wallet=False
            )
            
            if options.get('user_id'):
                wallets_query = wallets_query.filter(user_id=options['user_id'])
                self.stdout.write(f"Фильтр по пользователю ID: {options['user_id']}")
            
            wallets = wallets_query.select_related('user').all()
            self.stdout.write(f"Найдено кошельков: {len(wallets)}")
            
            # Статистика
            total_wallets = len(wallets)
            wallets_with_addresses = 0
            wallets_with_keys = 0
            wallets_with_balance = 0
            total_db_balance = Decimal('0')
            total_blockchain_balance = Decimal('0')
            issues_found = []
            
            for i, wallet in enumerate(wallets, 1):
                if not options.get('user_id') and total_wallets > 10:
                    # Для большого количества кошельков показываем краткую статистику
                    if wallet.deposit_address:
                        wallets_with_addresses += 1
                    if wallet.encrypted_private_key:
                        wallets_with_keys += 1
                    if wallet.balance > 0:
                        wallets_with_balance += 1
                        total_db_balance += wallet.balance
                    continue
                
                self.stdout.write(f"\n{i}. 👤 {wallet.user.email} (ID: {wallet.user.id})")
                self.stdout.write(f"   Кошелек ID: {wallet.id}")
                self.stdout.write(f"   Баланс в БД: {wallet.balance} SOL")
                self.stdout.write(f"   Доступный: {wallet.available_balance} SOL")
                self.stdout.write(f"   Заблокированный: {wallet.locked_balance} SOL")
                
                # Проверяем адрес
                if wallet.deposit_address:
                    self.stdout.write(f"   📍 Адрес: {wallet.deposit_address}")
                    wallets_with_addresses += 1
                    
                    # Проверяем баланс в блокчейне
                    if options.get('sync_balances') or options.get('check_transactions'):
                        try:
                            blockchain_balance = service.get_balance(wallet.deposit_address)
                            self.stdout.write(f"   💰 Баланс в блокчейне: {blockchain_balance} SOL")
                            total_blockchain_balance += blockchain_balance
                            
                            diff = blockchain_balance - wallet.balance
                            if abs(diff) > Decimal('0.001'):
                                self.stdout.write(f"   ⚠ Расхождение: {diff:+.6f} SOL")
                                issues_found.append(f"Баланс {wallet.user.email}: БД={wallet.balance}, блокчейн={blockchain_balance}")
                            
                        except Exception as e:
                            self.stdout.write(f"   ✗ Ошибка проверки баланса: {e}")
                    
                    # Проверяем транзакции
                    if options.get('check_transactions'):
                        try:
                            transactions = service.get_transactions(wallet.deposit_address)
                            self.stdout.write(f"   📋 Транзакций в блокчейне: {len(transactions)}")
                            
                            # Проверяем последние транзакции в БД
                            db_transactions = Transaction.objects.filter(
                                user=wallet.user,
                                crypto=sol_currency
                            ).count()
                            self.stdout.write(f"   📋 Транзакций в БД: {db_transactions}")
                            
                        except Exception as e:
                            self.stdout.write(f"   ✗ Ошибка проверки транзакций: {e}")
                            
                else:
                    self.stdout.write(f"   ⚠ Адрес отсутствует")
                    issues_found.append(f"Нет адреса: {wallet.user.email}")
                    
                    # Создаем адрес если запрошено
                    if options.get('fix_addresses'):
                        try:
                            new_address, private_key = service.create_new_address(user_id=wallet.user.id)
                            wallet.deposit_address = new_address
                            wallet.encrypted_private_key = private_key
                            wallet.save()
                            
                            self.stdout.write(f"   ✅ Создан адрес: {new_address}")
                            wallets_with_addresses += 1
                            
                        except Exception as e:
                            self.stdout.write(f"   ✗ Ошибка создания адреса: {e}")
                
                # Проверяем приватный ключ
                if wallet.encrypted_private_key:
                    self.stdout.write(f"   🔐 Приватный ключ: есть")
                    wallets_with_keys += 1
                else:
                    self.stdout.write(f"   ⚠ Приватный ключ: отсутствует")
                    if wallet.deposit_address:
                        issues_found.append(f"Нет приватного ключа: {wallet.user.email}")
                
                if wallet.balance > 0:
                    wallets_with_balance += 1
                    total_db_balance += wallet.balance
            
            # Итоговая статистика
            self.stdout.write(f"\n--- СТАТИСТИКА ---")
            self.stdout.write(f"Всего кошельков: {total_wallets}")
            self.stdout.write(f"С адресами: {wallets_with_addresses}")
            self.stdout.write(f"С приватными ключами: {wallets_with_keys}")
            self.stdout.write(f"С балансом > 0: {wallets_with_balance}")
            self.stdout.write(f"Общий баланс в БД: {total_db_balance} SOL")
            
            if options.get('sync_balances') and total_blockchain_balance > 0:
                self.stdout.write(f"Общий баланс в блокчейне: {total_blockchain_balance} SOL")
                balance_diff = total_blockchain_balance - total_db_balance
                self.stdout.write(f"Разница: {balance_diff:+.6f} SOL")
            
            if total_wallets > 0:
                coverage = (wallets_with_addresses / total_wallets) * 100
                self.stdout.write(f"Покрытие адресами: {coverage:.1f}%")
            
            # Проблемы
            if issues_found:
                self.stdout.write(f"\n--- НАЙДЕННЫЕ ПРОБЛЕМЫ ---")
                for issue in issues_found[:10]:  # Показываем первые 10
                    self.stdout.write(f"⚠ {issue}")
                if len(issues_found) > 10:
                    self.stdout.write(f"... и еще {len(issues_found) - 10} проблем")
            else:
                self.stdout.write(f"\n✅ Критических проблем не найдено")
            
            # Рекомендации
            self.stdout.write(f"\n--- РЕКОМЕНДАЦИИ ---")
            if wallets_with_addresses < total_wallets:
                missing = total_wallets - wallets_with_addresses
                self.stdout.write(f"• Создать адреса для {missing} кошельков: --fix-addresses")
            
            if not options.get('sync_balances'):
                self.stdout.write(f"• Проверить балансы: --sync-balances")
                
            if not options.get('check_transactions'):
                self.stdout.write(f"• Проверить транзакции: --check-transactions")
            
            # Транзакции консолидации
            consolidation_count = Transaction.objects.filter(
                type='consolidation',
                crypto=sol_currency
            ).count()
            self.stdout.write(f"\nТранзакций консолидации: {consolidation_count}")
            
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(self.style.ERROR("✗ Валюта SOL не найдена!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Критическая ошибка: {e}"))
            logger.exception("Критическая ошибка в check_solana_wallets")

        self.stdout.write(f"\n=== Диагностика завершена ===")