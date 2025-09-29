from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, UserWallet
from crypto.tasks_consolidation import consolidate_user_deposits
from crypto.blockchain.factory import get_blockchain_service
from transactions.models import Transaction
from accounts.models import User
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Тестирует консолидацию депозитов Solana'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze-only',
            action='store_true',
            help='Только анализ возможных консолидаций без выполнения',
        )
        parser.add_argument(
            '--force-run',
            action='store_true',
            help='Принудительно запустить консолидацию',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID пользователя для анализа конкретного кошелька',
        )

    def handle(self, *args, **options):
        self.stdout.write("=== Тестирование консолидации Solana ===\n")
        
        try:
            # Находим Solana валюту
            sol_currency = Cryptocurrency.objects.get(symbol__iexact='SOL', is_active=True)
            self.stdout.write(f"✓ Найдена валюта: {sol_currency.name} ({sol_currency.symbol})")
            self.stdout.write(f"  Сеть: {sol_currency.network}")
            self.stdout.write(f"  Требует MEMO: {sol_currency.requires_memo}")
            
            # Получаем блокчейн сервис
            service = get_blockchain_service(sol_currency.network or sol_currency.symbol)
            self.stdout.write(f"✓ Блокчейн сервис: {service.__class__.__name__}")
            
            # Находим системный кошелек
            try:
                system_wallet = UserWallet.objects.get(
                    currency=sol_currency,
                    is_system_wallet=True,
                    is_active=True
                )
                self.stdout.write(f"✓ Системный кошелек найден: ID={system_wallet.id}")
                self.stdout.write(f"  Баланс в БД: {system_wallet.balance} SOL")
                self.stdout.write(f"  Адрес: {system_wallet.deposit_address}")
                
                # Проверяем баланс в блокчейне
                if system_wallet.deposit_address:
                    try:
                        blockchain_balance = service.get_balance(system_wallet.deposit_address)
                        self.stdout.write(f"  Баланс в блокчейне: {blockchain_balance} SOL")
                    except Exception as e:
                        self.stdout.write(f"  ⚠ Ошибка получения баланса: {e}")
                
            except UserWallet.DoesNotExist:
                self.stdout.write(self.style.ERROR("✗ Системный кошелек не найден!"))
                return
            
            # Анализируем пользовательские кошельки
            self.stdout.write(f"\n--- Анализ пользовательских кошельков ---")
            
            user_wallets_query = UserWallet.objects.filter(
                currency=sol_currency,
                is_system_wallet=False,
                deposit_address__isnull=False,
                encrypted_private_key__isnull=False
            ).exclude(deposit_address='')
            
            if options.get('user_id'):
                user_wallets_query = user_wallets_query.filter(user_id=options['user_id'])
                self.stdout.write(f"Фильтр по пользователю ID: {options['user_id']}")
            
            user_wallets = user_wallets_query.all()
            self.stdout.write(f"Найдено пользовательских кошельков с адресами: {len(user_wallets)}")
            
            consolidation_candidates = []
            total_amount_to_consolidate = Decimal('0')
            
            for wallet in user_wallets:
                self.stdout.write(f"\n👤 Пользователь: {wallet.user.email} (ID: {wallet.user.id})")
                self.stdout.write(f"   Адрес: {wallet.deposit_address}")
                self.stdout.write(f"   Баланс в БД: {wallet.balance} SOL")
                
                try:
                    # Проверяем баланс в блокчейне
                    blockchain_balance = service.get_balance(wallet.deposit_address)
                    self.stdout.write(f"   Баланс в блокчейне: {blockchain_balance} SOL")
                    
                    # Проверяем минимальную сумму для консолидации
                    from crypto.tasks_consolidation import get_min_consolidation_amount, get_gas_reserve
                    min_amount = get_min_consolidation_amount(sol_currency)
                    gas_reserve = get_gas_reserve(sol_currency)
                    
                    self.stdout.write(f"   Минимум для консолидации: {min_amount} SOL")
                    self.stdout.write(f"   Резерв на газ: {gas_reserve} SOL")
                    
                    if blockchain_balance >= min_amount:
                        amount_to_send = blockchain_balance - gas_reserve
                        if amount_to_send > 0:
                            consolidation_candidates.append({
                                'wallet': wallet,
                                'blockchain_balance': blockchain_balance,
                                'amount_to_send': amount_to_send
                            })
                            total_amount_to_consolidate += amount_to_send
                            self.stdout.write(f"   ✅ ПОДХОДИТ для консолидации: {amount_to_send} SOL")
                        else:
                            self.stdout.write(f"   ❌ Недостаточно средств после резерва на газ")
                    else:
                        self.stdout.write(f"   ❌ Ниже минимума для консолидации")
                    
                except Exception as e:
                    self.stdout.write(f"   ⚠ Ошибка проверки баланса: {e}")
            
            # Итоги анализа
            self.stdout.write(f"\n--- ИТОГИ АНАЛИЗА ---")
            self.stdout.write(f"Кандидатов на консолидацию: {len(consolidation_candidates)}")
            self.stdout.write(f"Общая сумма к консолидации: {total_amount_to_consolidate} SOL")
            
            if consolidation_candidates:
                self.stdout.write(f"\nДетали кандидатов:")
                for i, candidate in enumerate(consolidation_candidates, 1):
                    wallet = candidate['wallet']
                    self.stdout.write(f"  {i}. {wallet.user.email}: {candidate['amount_to_send']} SOL")
            
            # Выполнение консолидации если запрошено
            if options.get('force_run') and not options.get('analyze_only'):
                if consolidation_candidates:
                    self.stdout.write(f"\n🚀 Запуск консолидации...")
                    
                    # Проверим количество транзакций до
                    before_count = Transaction.objects.filter(
                        type='consolidation',
                        crypto=sol_currency
                    ).count()
                    
                    try:
                        result = consolidate_user_deposits()
                        self.stdout.write(f"✅ Результат: {result}")
                        
                        # Проверим количество после
                        after_count = Transaction.objects.filter(
                            type='consolidation',
                            crypto=sol_currency
                        ).count()
                        
                        new_transactions = after_count - before_count
                        if new_transactions > 0:
                            self.stdout.write(f"✅ Создано новых транзакций консолидации: {new_transactions}")
                            
                            # Показываем последние транзакции
                            latest_txs = Transaction.objects.filter(
                                type='consolidation',
                                crypto=sol_currency
                            ).order_by('-timestamp')[:new_transactions]
                            
                            for tx in latest_txs:
                                self.stdout.write(f"  TX: {tx.tx_hash}")
                                self.stdout.write(f"      Сумма: {tx.amount} SOL")
                                self.stdout.write(f"      Пользователь: {tx.user.email}")
                                if tx.tx_hash:
                                    self.stdout.write(f"      Explorer: https://explorer.solana.com/tx/{tx.tx_hash}?cluster=devnet")
                        else:
                            self.stdout.write(f"⚠ Новых транзакций не создано")
                            
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"✗ Ошибка консолидации: {e}"))
                else:
                    self.stdout.write(f"ℹ Нет кандидатов для консолидации")
            elif options.get('analyze_only'):
                self.stdout.write(f"\nℹ Анализ завершен (только просмотр)")
            else:
                self.stdout.write(f"\nℹ Для запуска консолидации используйте --force-run")
                
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(self.style.ERROR("✗ Валюта SOL не найдена!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Критическая ошибка: {e}"))
            logger.exception("Критическая ошибка в test_solana_consolidation")

        self.stdout.write(f"\n=== Тест завершён ===")