"""
Команда для принудительной синхронизации баланса системного кошелька SOL с блокчейном
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import logging

from crypto.models import Cryptocurrency, SystemWalletBalanceLog, UserWallet
from crypto.tasks_consolidation import get_system_wallet_address
from crypto.blockchain.factory import get_blockchain_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Принудительно синхронизирует баланс системного кошелька SOL с блокчейном'

    def add_arguments(self, parser):
        parser.add_argument(
            '--currency',
            type=str,
            default='SOL',
            help='Символ валюты для синхронизации (по умолчанию SOL)'
        )
        parser.add_argument(
            '--network',
            type=str,
            help='Сеть для синхронизации (если не указана, используется сеть валюты)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительно синхронизировать даже если балансы совпадают'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет синхронизировано без фактического изменения'
        )

    def handle(self, *args, **options):
        currency_symbol = options['currency'].upper()
        network = options.get('network')
        force = options.get('force', False)
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(f"=== Синхронизация баланса системного кошелька {currency_symbol} ===\n")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 РЕЖИМ ПРОСМОТРА - изменения не будут сохранены"))
        
        try:
            # Получаем валюту
            if network:
                currency = Cryptocurrency.objects.get(
                    symbol=currency_symbol, 
                    network=network,
                    is_active=True
                )
            else:
                currency = Cryptocurrency.objects.filter(
                    symbol=currency_symbol,
                    is_active=True
                ).first()
                
                if not currency:
                    self.stdout.write(
                        self.style.ERROR(f"Валюта {currency_symbol} не найдена")
                    )
                    return
                    
                network = currency.network or currency_symbol
            
            self.stdout.write(f"Валюта: {currency.name} ({currency.symbol})")
            self.stdout.write(f"Сеть: {network}")
            
            # Получаем адрес системного кошелька
            system_wallet_address = get_system_wallet_address(currency)
            self.stdout.write(f"Системный адрес: {system_wallet_address}")
            
            # Получаем сервис блокчейна
            service = get_blockchain_service(network)
            
            # Получаем баланс из блокчейна
            blockchain_balance = service.get_balance(system_wallet_address)
            self.stdout.write(f"Баланс в блокчейне: {blockchain_balance} {currency.symbol}")
            
            # Получаем баланс из БД
            try:
                system_wallet = UserWallet.objects.get(
                    user=None,
                    currency=currency,
                    is_system_wallet=True,
                    is_active=True
                )
                database_balance = system_wallet.balance
                self.stdout.write(f"Баланс в БД: {database_balance} {currency.symbol}")
                
                # Проверяем необходимость синхронизации
                diff = blockchain_balance - database_balance
                if diff == 0 and not force:
                    self.stdout.write(self.style.SUCCESS("✓ Балансы уже синхронизированы"))
                    if not dry_run:
                        # Логируем без синхронизации
                        SystemWalletBalanceLog.log_system_wallet_balance(
                            currency=currency,
                            system_address=system_wallet_address,
                            blockchain_balance=blockchain_balance,
                            transaction_type='manual_check',
                            notes='Balance sync check - already synchronized',
                            sync_balance=False
                        )
                    return
                
                # Показываем что будет изменено
                if diff > 0:
                    self.stdout.write(self.style.WARNING(f"⚠ Блокчейн больше на {diff} {currency.symbol}"))
                    action = "Увеличить"
                elif diff < 0:
                    self.stdout.write(self.style.WARNING(f"⚠ БД больше на {abs(diff)} {currency.symbol}"))
                    action = "Уменьшить"
                else:
                    self.stdout.write("Балансы равны, но принудительная синхронизация запрошена")
                    action = "Обновить"
                
                if dry_run:
                    self.stdout.write(f"🔍 БУДЕТ ВЫПОЛНЕНО: {action} баланс БД с {database_balance} до {blockchain_balance} {currency.symbol}")
                    return
                
                # Выполняем синхронизацию
                old_balance = system_wallet.balance
                system_wallet.balance = blockchain_balance
                system_wallet.available_balance = blockchain_balance - system_wallet.locked_balance
                system_wallet.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Баланс синхронизирован: {old_balance} -> {blockchain_balance} {currency.symbol}"
                    )
                )
                
                # Логируем синхронизацию
                balance_log = SystemWalletBalanceLog.log_system_wallet_balance(
                    currency=currency,
                    system_address=system_wallet_address,
                    blockchain_balance=blockchain_balance,
                    transaction_type='system_update',
                    notes=f'Manual sync: {action} balance by {abs(diff)} {currency.symbol}',
                    sync_balance=False  # Уже синхронизировали выше
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Синхронизация залогирована (ID: {balance_log.id})"
                    )
                )
                
            except UserWallet.DoesNotExist:
                self.stdout.write(self.style.ERROR("⚠ Системный кошелек не найден в БД"))
                self.stdout.write("Создайте системный кошелек через админку или команду создания кошельков")
                return
            
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Валюта {currency_symbol} не найдена в БД")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Ошибка при синхронизации: {e}")
            )
            logger.exception("Ошибка при синхронизации баланса системного кошелька")
        
        self.stdout.write("\n=== Синхронизация завершена ===")
