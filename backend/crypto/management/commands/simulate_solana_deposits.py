from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from crypto.models import Cryptocurrency, UserWallet
from transactions.models import Transaction
from crypto.tasks import check_blockchain_deposits
from crypto.tasks_consolidation import consolidate_user_deposits
from decimal import Decimal
from django.utils import timezone
import uuid
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Имитирует Solana депозиты для тестирования консолидации'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email пользователя для создания депозита',
        )
        parser.add_argument(
            '--amount',
            type=str,
            default='0.05',
            help='Сумма депозита в SOL (по умолчанию: 0.05)',
        )
        parser.add_argument(
            '--auto-consolidate',
            action='store_true',
            help='Автоматически запустить консолидацию после создания депозита',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='Количество депозитов для создания (по умолчанию: 1)',
        )

    def handle(self, *args, **options):
        self.stdout.write("=== Имитация Solana депозитов ===\n")
        
        try:
            # Находим Solana валюту
            sol_currency = Cryptocurrency.objects.get(symbol__iexact='SOL', is_active=True)
            self.stdout.write(f"✓ Найдена валюта: {sol_currency.name} ({sol_currency.symbol})")
            
            # Определяем сумму депозита
            try:
                deposit_amount = Decimal(options['amount'])
                if deposit_amount <= 0:
                    raise ValueError("Сумма должна быть положительной")
                self.stdout.write(f"✓ Сумма депозита: {deposit_amount} SOL")
            except (ValueError, TypeError) as e:
                self.stdout.write(self.style.ERROR(f"✗ Неверная сумма: {e}"))
                return
            
            # Определяем пользователей
            if options.get('user_email'):
                try:
                    users = [User.objects.get(email=options['user_email'])]
                    self.stdout.write(f"✓ Пользователь: {options['user_email']}")
                except User.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"✗ Пользователь {options['user_email']} не найден"))
                    return
            else:
                # Берем первых пользователей с SOL кошельками
                users = User.objects.filter(
                    wallets__currency=sol_currency,
                    wallets__is_system_wallet=False,
                    wallets__deposit_address__isnull=False
                ).distinct()[:options['count']]
                
                if not users:
                    self.stdout.write(self.style.ERROR("✗ Не найдено пользователей с SOL кошельками"))
                    return
                    
                self.stdout.write(f"✓ Найдено пользователей: {len(users)}")
            
            # Получаем системный кошелек
            try:
                system_wallet = UserWallet.objects.get(
                    currency=sol_currency,
                    is_system_wallet=True,
                    is_active=True
                )
                self.stdout.write(f"✓ Системный кошелек: баланс {system_wallet.balance} SOL")
            except UserWallet.DoesNotExist:
                self.stdout.write(self.style.ERROR("✗ Системный кошелек не найден"))
                return
            
            # Создаем депозиты
            created_deposits = []
            total_deposited = Decimal('0')
            
            for i, user in enumerate(users[:options['count']], 1):
                self.stdout.write(f"\n{i}. 👤 Пользователь: {user.email}")
                
                try:
                    # Находим кошелек пользователя
                    user_wallet = UserWallet.objects.get(
                        user=user,
                        currency=sol_currency,
                        is_system_wallet=False
                    )
                    
                    if not user_wallet.deposit_address:
                        self.stdout.write(f"   ⚠ У пользователя нет депозитного адреса")
                        continue
                    
                    self.stdout.write(f"   📍 Адрес: {user_wallet.deposit_address}")
                    self.stdout.write(f"   💰 Баланс до: {user_wallet.balance} SOL")
                    
                    # Генерируем уникальный tx_hash
                    fake_tx_hash = f"SOL_TEST_{uuid.uuid4().hex[:16]}"
                    
                    # Создаем транзакцию депозита
                    deposit_tx = Transaction.objects.create(
                        user=user,
                        type='deposit',
                        status='completed',
                        amount=deposit_amount,
                        fee=Decimal('0'),
                        crypto=sol_currency,
                        tx_hash=fake_tx_hash,
                        timestamp=timezone.now(),
                        notes=f"Test deposit via simulate_solana_deposits command"
                    )
                    
                    # Обновляем баланс пользователя
                    user_wallet.balance += deposit_amount
                    user_wallet.available_balance = user_wallet.balance - user_wallet.locked_balance
                    user_wallet.save()
                    
                    # Обновляем баланс системного кошелька
                    system_wallet.balance += deposit_amount
                    system_wallet.available_balance = system_wallet.balance - system_wallet.locked_balance
                    system_wallet.save()
                    
                    created_deposits.append({
                        'user': user,
                        'transaction': deposit_tx,
                        'amount': deposit_amount
                    })
                    total_deposited += deposit_amount
                    
                    self.stdout.write(f"   ✅ Депозит создан: {deposit_amount} SOL")
                    self.stdout.write(f"   💰 Баланс после: {user_wallet.balance} SOL")
                    self.stdout.write(f"   🔗 TX Hash: {fake_tx_hash}")
                    
                except UserWallet.DoesNotExist:
                    self.stdout.write(f"   ✗ Кошелек SOL не найден для пользователя")
                    continue
                except Exception as e:
                    self.stdout.write(f"   ✗ Ошибка создания депозита: {e}")
                    logger.exception(f"Ошибка создания депозита для пользователя {user.id}")
                    continue
            
            # Итоги создания депозитов
            self.stdout.write(f"\n--- ИТОГИ ДЕПОЗИТОВ ---")
            self.stdout.write(f"Создано депозитов: {len(created_deposits)}")
            self.stdout.write(f"Общая сумма: {total_deposited} SOL")
            self.stdout.write(f"Системный кошелек: {system_wallet.balance} SOL")
            
            # Автоматическая консолидация если запрошена
            if options.get('auto_consolidate') and created_deposits:
                self.stdout.write(f"\n🚀 Запуск автоматической консолидации...")
                
                # Проверяем количество транзакций консолидации до
                before_consolidations = Transaction.objects.filter(
                    type='consolidation',
                    crypto=sol_currency
                ).count()
                
                try:
                    # Запускаем консолидацию
                    result = consolidate_user_deposits()
                    self.stdout.write(f"✅ Результат консолидации: {result}")
                    
                    # Проверяем количество после
                    after_consolidations = Transaction.objects.filter(
                        type='consolidation',
                        crypto=sol_currency
                    ).count()
                    
                    new_consolidations = after_consolidations - before_consolidations
                    if new_consolidations > 0:
                        self.stdout.write(f"✅ Создано новых консолидаций: {new_consolidations}")
                        
                        # Показываем последние транзакции консолидации
                        latest_consolidations = Transaction.objects.filter(
                            type='consolidation',
                            crypto=sol_currency
                        ).order_by('-timestamp')[:new_consolidations]
                        
                        for tx in latest_consolidations:
                            self.stdout.write(f"  📤 {tx.user.email}: {tx.amount} SOL")
                            if tx.tx_hash:
                                self.stdout.write(f"      TX: {tx.tx_hash}")
                                self.stdout.write(f"      Explorer: https://explorer.solana.com/tx/{tx.tx_hash}?cluster=devnet")
                    else:
                        self.stdout.write(f"⚠ Новых консолидаций не создано")
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ Ошибка консолидации: {e}"))
                    
            elif created_deposits:
                self.stdout.write(f"\nℹ Для запуска консолидации используйте --auto-consolidate")
                self.stdout.write(f"  Или запустите: python manage.py test_solana_consolidation --force-run")
            
            # Дополнительная информация
            if created_deposits:
                self.stdout.write(f"\n📋 Созданные депозиты:")
                for deposit in created_deposits:
                    self.stdout.write(f"  • {deposit['user'].email}: {deposit['amount']} SOL")
                    self.stdout.write(f"    TX: {deposit['transaction'].tx_hash}")
                
                self.stdout.write(f"\n💡 Полезные команды:")
                self.stdout.write(f"  python manage.py test_solana_consolidation --analyze-only")
                self.stdout.write(f"  python manage.py test_solana_consolidation --force-run")
                self.stdout.write(f"  python manage.py check_blockchain_deposits  # реальное сканирование")
            
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(self.style.ERROR("✗ Валюта SOL не найдена!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Критическая ошибка: {e}"))
            logger.exception("Критическая ошибка в simulate_solana_deposits")

        self.stdout.write(f"\n=== Имитация завершена ===")