from django.core.management.base import BaseCommand
from transactions.models import Withdrawal, Transaction, Transfer
from crypto.models import Cryptocurrency, UserWallet
from accounts.models import User
from crypto.tasks import process_withdrawal
from decimal import Decimal
import uuid
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Тестирует различные сценарии незавершённых транзакций Solana'

    def add_arguments(self, parser):
        parser.add_argument(
            '--scenario',
            type=str,
            choices=['success', 'insufficient_funds', 'invalid_address', 'network_error'],
            default='success',
            help='Сценарий для тестирования',
        )

    def handle(self, *args, **options):
        scenario = options['scenario']
        self.stdout.write(f"=== Тест незавершённых транзакций Solana: {scenario} ===\n")
        
        try:
            # Получаем необходимые объекты
            sol = Cryptocurrency.objects.get(symbol__iexact='SOL', is_active=True)
            user = User.objects.first()
            user_wallet = UserWallet.objects.filter(user=user, currency=sol).first()
            system_wallet = UserWallet.objects.get(currency=sol, is_system_wallet=True)
            
            if not user_wallet:
                user_wallet = UserWallet.objects.create(
                    user=user,
                    currency=sol,
                    balance=Decimal('0.1'),
                    available_balance=Decimal('0.1'),
                    is_active=True
                )
                self.stdout.write(f"✓ Создан кошелёк пользователя с балансом 0.1 SOL")
            
            self.stdout.write(f"Пользователь: {user.email}")
            self.stdout.write(f"Баланс пользователя: {user_wallet.balance} SOL")
            self.stdout.write(f"Баланс системного кошелька: {system_wallet.balance} SOL")
            
            # Подготовка к различным сценариям
            if scenario == 'insufficient_funds':
                # Временно уменьшаем баланс системного кошелька
                original_balance = system_wallet.balance
                system_wallet.balance = Decimal('0.001')
                system_wallet.available_balance = Decimal('0.001') 
                system_wallet.save()
                self.stdout.write(f"⚠ Временно уменьшен баланс системного кошелька до {system_wallet.balance} SOL")
                test_address = "GkVvtMDQ5v1ReiScLQAf45B2X3H1WXr8hrJoY7jcqddQ"
                test_amount = Decimal('0.02')
                
            elif scenario == 'invalid_address':
                test_address = "InvalidSolanaAddress123"
                test_amount = Decimal('0.001')
                
            elif scenario == 'network_error':
                # Для тестирования сетевых ошибок можно временно изменить RPC endpoint
                test_address = "GkVvtMDQ5v1ReiScLQAf45B2X3H1WXr8hrJoY7jcqddQ"
                test_amount = Decimal('0.001')
                self.stdout.write("⚠ Будет тестироваться обработка сетевых ошибок")
                
            else:  # success
                test_address = "GkVvtMDQ5v1ReiScLQAf45B2X3H1WXr8hrJoY7jcqddQ"
                test_amount = Decimal('0.001')
            
            # Создаем тестовую транзакцию
            tx = Transaction.objects.create(
                user=user,
                type='withdrawal',
                status='pending',
                amount=test_amount,
                fee=Decimal('0.0001'),
                crypto=sol,
                notes=f'Test {scenario} withdrawal'
            )
            
            withdrawal = Withdrawal.objects.create(
                user=user,
                transaction=tx,
                wallet=user_wallet,
                destination_address=test_address,
                is_email_confirmed=True
            )
            
            transfer = Transfer.objects.create(
                user=user,
                type='out',
                amount=test_amount,
                status='pending'
            )
            
            self.stdout.write(f"✓ Создана тестовая транзакция:")
            self.stdout.write(f"  Transaction ID: {tx.id}")
            self.stdout.write(f"  Withdrawal ID: {withdrawal.id}")
            self.stdout.write(f"  Transfer ID: {transfer.id}")
            self.stdout.write(f"  Сумма: {test_amount} SOL")
            self.stdout.write(f"  Адрес получателя: {test_address}")
            
            # Обрабатываем транзакцию
            self.stdout.write(f"\n--- Обработка транзакции ---")
            try:
                result = process_withdrawal.apply(args=[transfer.id])
                self.stdout.write(f"Результат обработки: {result.result}")
                
                # Проверяем финальное состояние
                transfer.refresh_from_db()
                tx.refresh_from_db()
                
                self.stdout.write(f"\n--- Финальное состояние ---")
                self.stdout.write(f"Transfer статус: {transfer.status}")
                self.stdout.write(f"Transaction статус: {tx.status}")
                if transfer.tx_hash:
                    self.stdout.write(f"TX Hash: {transfer.tx_hash}")
                    self.stdout.write(f"Explorer: https://explorer.solana.com/tx/{transfer.tx_hash}?cluster=devnet")
                
                if transfer.status == 'success':
                    self.stdout.write(self.style.SUCCESS("✓ Транзакция успешно завершена"))
                elif transfer.status == 'failed':
                    self.stdout.write(self.style.ERROR("✗ Транзакция завершилась с ошибкой"))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Критическая ошибка при обработке: {e}"))
                logger.exception("Критическая ошибка в тесте транзакции")
            
            # Восстанавливаем баланс системного кошелька если изменяли
            if scenario == 'insufficient_funds':
                system_wallet.balance = original_balance
                system_wallet.available_balance = original_balance
                system_wallet.save()
                self.stdout.write(f"\n✓ Восстановлен баланс системного кошелька: {original_balance} SOL")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Критическая ошибка: {e}"))
            logger.exception("Критическая ошибка в test_incomplete_transaction")

        self.stdout.write(f"\n=== Тест завершён ===")
        self.stdout.write(f"\nДля тестирования других сценариев:")
        self.stdout.write(f"python manage.py test_incomplete_transaction --scenario=success")
        self.stdout.write(f"python manage.py test_incomplete_transaction --scenario=insufficient_funds")
        self.stdout.write(f"python manage.py test_incomplete_transaction --scenario=invalid_address")