"""
Команда для ручной проверки и логирования баланса системного кошелька SOL
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import logging

from crypto.models import Cryptocurrency, SystemWalletBalanceLog
from crypto.tasks_consolidation import get_system_wallet_address
from crypto.blockchain.factory import get_blockchain_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Проверяет и логирует баланс системного кошелька SOL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--currency',
            type=str,
            default='SOL',
            help='Символ валюты для проверки (по умолчанию SOL)'
        )
        parser.add_argument(
            '--network',
            type=str,
            help='Сеть для проверки (если не указана, используется сеть валюты)'
        )
        parser.add_argument(
            '--notes',
            type=str,
            default='Manual balance check',
            help='Примечание для лога'
        )
        parser.add_argument(
            '--show-details',
            action='store_true',
            help='Показать детальную информацию о последних операциях'
        )
        parser.add_argument(
            '--last-n',
            type=int,
            default=5,
            help='Количество последних записей для показа (по умолчанию 5)'
        )

    def handle(self, *args, **options):
        currency_symbol = options['currency'].upper()
        network = options.get('network')
        notes = options['notes']
        show_details = options.get('show_details', False)
        last_n = options.get('last_n', 5)
        
        self.stdout.write(f"=== Проверка баланса системного кошелька {currency_symbol} ===\n")
        
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
            self.stdout.write(f"Активна: {'Да' if currency.is_active else 'Нет'}")
            
            # Получаем адрес системного кошелька
            system_wallet_address = get_system_wallet_address(currency)
            self.stdout.write(f"Системный адрес: {system_wallet_address}")
            
            # Получаем сервис блокчейна
            service = get_blockchain_service(network)
            
            # Получаем баланс из блокчейна
            blockchain_balance = service.get_balance(system_wallet_address)
            self.stdout.write(f"Баланс в блокчейне: {blockchain_balance} {currency.symbol}")
            
            # Получаем баланс из БД для сравнения
            try:
                from crypto.models import UserWallet
                system_wallet = UserWallet.objects.get(
                    user=None,
                    currency=currency,
                    is_system_wallet=True,
                    is_active=True
                )
                database_balance = system_wallet.balance
                self.stdout.write(f"Баланс в БД: {database_balance} {currency.symbol}")
                
                # Показываем разность
                diff = blockchain_balance - database_balance
                if diff == 0:
                    self.stdout.write(self.style.SUCCESS("✓ Балансы синхронизированы"))
                elif diff > 0:
                    self.stdout.write(self.style.WARNING(f"⚠ Блокчейн больше на {diff} {currency.symbol}"))
                else:
                    self.stdout.write(self.style.WARNING(f"⚠ БД больше на {abs(diff)} {currency.symbol}"))
                    
            except UserWallet.DoesNotExist:
                self.stdout.write(self.style.WARNING("⚠ Системный кошелек не найден в БД"))
                database_balance = None
            
            # Логируем баланс (синхронизируем только если есть расхождения)
            should_sync = database_balance is not None and database_balance != blockchain_balance
            balance_log = SystemWalletBalanceLog.log_system_wallet_balance(
                currency=currency,
                system_address=system_wallet_address,
                blockchain_balance=blockchain_balance,
                transaction_type='manual_check',
                notes=notes,
                sync_balance=should_sync
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Баланс залогирован в БД (ID: {balance_log.id})"
                )
            )
            
            # Показываем последние записи
            recent_logs = SystemWalletBalanceLog.objects.filter(
                currency=currency
            ).order_by('-created_at')[:last_n]
            
            if recent_logs:
                self.stdout.write(f"\n--- Последние {last_n} записей ---")
                for log in recent_logs:
                    diff_info = ""
                    if log.database_balance is not None:
                        diff = log.blockchain_balance - log.database_balance
                        if diff == 0:
                            diff_info = " (синхронизирован)"
                        else:
                            diff_info = f" (разность: {diff:+.8f})"
                    
                    self.stdout.write(
                        f"{log.created_at.strftime('%Y-%m-%d %H:%M:%S')} | "
                        f"{log.blockchain_balance} {currency.symbol} | "
                        f"{log.get_transaction_type_display()}{diff_info}"
                    )
                    
                    # Показываем детали если запрошено
                    if show_details and log.notes:
                        self.stdout.write(f"  Примечания: {log.notes}")
                    if show_details and log.related_transaction:
                        self.stdout.write(f"  Транзакция: {log.related_transaction.tx_hash}")
            
            # Статистика по типам транзакций
            if show_details:
                from django.db.models import Count
                stats = SystemWalletBalanceLog.objects.filter(
                    currency=currency
                ).values('transaction_type').annotate(
                    count=Count('id')
                ).order_by('-count')
                
                if stats:
                    self.stdout.write(f"\n--- Статистика по типам транзакций ---")
                    for stat in stats:
                        type_display = dict(SystemWalletBalanceLog.TRANSACTION_TYPE_CHOICES)[stat['transaction_type']]
                        self.stdout.write(f"{type_display}: {stat['count']} операций")
            
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Валюта {currency_symbol} не найдена в БД")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Ошибка при проверке баланса: {e}")
            )
            logger.exception("Ошибка при проверке баланса системного кошелька")
        
        self.stdout.write("\n=== Проверка завершена ===")
