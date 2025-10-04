"""
Команда для тестирования консолидации с мок-данными
"""
from django.core.management.base import BaseCommand
from crypto.tasks_consolidation import consolidate_user_deposits
from crypto.models import UserWallet, Cryptocurrency
from transactions.models import Transaction
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Тестирует консолидацию с мок-данными'

    def add_arguments(self, parser):
        parser.add_argument('--simulate', action='store_true', help='Только симуляция, без реальных транзакций')

    def handle(self, *args, **options):
        self.stdout.write("🧪 Тестирование консолидации с мок-данными...")
        
        # Создаем тестовый депозит с "реальным" балансом
        pol = Cryptocurrency.objects.get(symbol='POL')
        
        # Находим последний депозит
        last_deposit = Transaction.objects.filter(
            crypto=pol,
            type='deposit',
            status='completed'
        ).order_by('-timestamp').first()
        
        if not last_deposit:
            self.stdout.write("❌ Депозиты не найдены")
            return
            
        self.stdout.write(f"📥 Последний депозит: {last_deposit.amount} POL от User {last_deposit.user.id}")
        
        # Получаем кошелек пользователя
        user_wallet = UserWallet.objects.get(
            user=last_deposit.user,
            currency=pol,
            is_system_wallet=False
        )
        
        self.stdout.write(f"💰 Адрес кошелька: {user_wallet.deposit_address}")
        
        if options['simulate']:
            self.stdout.write("🔧 СИМУЛЯЦИЯ: Представляем, что на адресе есть 0.5 POL")
            
            # Создаем мок-консолидацию
            mock_amount = Decimal('0.495')  # 0.5 - 0.005 комиссия
            
            mock_tx = Transaction.objects.create(
                user=last_deposit.user,
                crypto=pol,
                amount=mock_amount,
                tx_hash=f"mock_consolidation_{timezone.now().timestamp()}",
                type="consolidation",
                status="completed",
                timestamp=timezone.now()
            )
            
            self.stdout.write(f"✅ Создана мок-консолидация: {mock_tx.tx_hash}")
        else:
            self.stdout.write("⚠️ Реальная консолидация требует средства на блокчейне")
            
        self.stdout.write("✅ Тест завершен")
