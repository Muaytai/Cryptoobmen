"""
Команда для проверки балансов всех активных системных кошельков
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
    help = 'Проверяет балансы всех активных системных кошельков'

    def add_arguments(self, parser):
        parser.add_argument(
            '--network',
            type=str,
            help='Проверить только указанную сеть (например, SOL, Polygon)'
        )
        parser.add_argument(
            '--skip-zero',
            action='store_true',
            help='Пропустить кошельки с нулевым балансом'
        )
        parser.add_argument(
            '--log-balances',
            action='store_true',
            help='Логировать балансы в SystemWalletBalanceLog'
        )

    def handle(self, *args, **options):
        network_filter = options.get('network')
        skip_zero = options.get('skip_zero', False)
        log_balances = options.get('log_balances', False)
        
        self.stdout.write("=== Проверка всех активных системных кошельков ===\n")
        
        # Получаем все активные валюты
        currencies = Cryptocurrency.objects.filter(is_active=True)
        
        if network_filter:
            currencies = currencies.filter(network__icontains=network_filter)
            self.stdout.write(f"Фильтр по сети: {network_filter}")
        
        if not currencies.exists():
            self.stdout.write(self.style.WARNING("Активные валюты не найдены"))
            return
        
        total_checked = 0
        total_issues = 0
        results = []
        
        for currency in currencies:
            try:
                self.stdout.write(f"\n--- {currency.name} ({currency.symbol}) ---")
                
                # Получаем адрес системного кошелька
                try:
                    system_wallet_address = get_system_wallet_address(currency)
                    self.stdout.write(f"Адрес: {system_wallet_address}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Ошибка получения адреса: {e}"))
                    total_issues += 1
                    continue
                
                # Получаем сервис блокчейна
                try:
                    network = currency.network or currency.symbol
                    service = get_blockchain_service(network)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Ошибка подключения к сети {network}: {e}"))
                    total_issues += 1
                    continue
                
                # Получаем баланс из блокчейна
                try:
                    blockchain_balance = service.get_balance(system_wallet_address)
                    self.stdout.write(f"Баланс в блокчейне: {blockchain_balance} {currency.symbol}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Ошибка получения баланса: {e}"))
                    total_issues += 1
                    continue
                
                # Пропускаем нулевые балансы если запрошено
                if skip_zero and blockchain_balance == 0:
                    self.stdout.write("Пропущен (нулевой баланс)")
                    continue
                
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
                    
                    # Проверяем синхронизацию
                    diff = blockchain_balance - database_balance
                    if diff == 0:
                        self.stdout.write(self.style.SUCCESS("✓ Синхронизирован"))
                        status = "OK"
                    elif diff > 0:
                        self.stdout.write(self.style.WARNING(f"⚠ Блокчейн больше на {diff} {currency.symbol}"))
                        status = "BLOCKCHAIN_HIGHER"
                        total_issues += 1
                    else:
                        self.stdout.write(self.style.WARNING(f"⚠ БД больше на {abs(diff)} {currency.symbol}"))
                        status = "DATABASE_HIGHER"
                        total_issues += 1
                        
                except UserWallet.DoesNotExist:
                    self.stdout.write(self.style.WARNING("⚠ Системный кошелек не найден в БД"))
                    database_balance = None
                    status = "NOT_IN_DB"
                    total_issues += 1
                
                # Логируем баланс если запрошено (синхронизируем только при расхождениях)
                if log_balances:
                    try:
                        should_sync = status in ['BLOCKCHAIN_HIGHER', 'DATABASE_HIGHER', 'NOT_IN_DB']
                        balance_log = SystemWalletBalanceLog.log_system_wallet_balance(
                            currency=currency,
                            system_address=system_wallet_address,
                            blockchain_balance=blockchain_balance,
                            transaction_type='manual_check',
                            notes=f'Bulk check - {status}',
                            sync_balance=should_sync
                        )
                        sync_info = " (синхронизирован)" if should_sync else ""
                        self.stdout.write(f"Логирован (ID: {balance_log.id}){sync_info}")
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Ошибка логирования: {e}"))
                
                results.append({
                    'currency': f"{currency.symbol} ({currency.network or currency.symbol})",
                    'blockchain_balance': blockchain_balance,
                    'database_balance': database_balance,
                    'status': status
                })
                
                total_checked += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Общая ошибка для {currency.symbol}: {e}"))
                total_issues += 1
        
        # Итоговая статистика
        self.stdout.write(f"\n=== Итоги ===")
        self.stdout.write(f"Проверено кошельков: {total_checked}")
        self.stdout.write(f"Найдено проблем: {total_issues}")
        
        if total_issues == 0:
            self.stdout.write(self.style.SUCCESS("✓ Все кошельки в порядке!"))
        else:
            self.stdout.write(self.style.WARNING("⚠ Обнаружены проблемы с синхронизацией"))
            
            # Показываем проблемные кошельки
            self.stdout.write(f"\n--- Проблемные кошельки ---")
            for result in results:
                if result['status'] != 'OK':
                    self.stdout.write(f"{result['currency']}: {result['status']}")
        
        # Показываем кошельки с балансом > 0
        active_wallets = [r for r in results if r['blockchain_balance'] > 0]
        if active_wallets:
            self.stdout.write(f"\n--- Кошельки с балансом > 0 ---")
            for result in active_wallets:
                self.stdout.write(f"{result['currency']}: {result['blockchain_balance']}")
        
        self.stdout.write("\n=== Проверка завершена ===")
