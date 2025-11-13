from django.core.management.base import BaseCommand
from crypto.tasks_consolidation import consolidate_user_deposits, check_consolidation_confirmations
from crypto.models import UserWallet, Cryptocurrency
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Тестировать консолидацию депозитов'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Показать что будет сделано без выполнения')
        parser.add_argument('--currency', type=str, help='Тестировать только указанную валюту')
        parser.add_argument('--check-confirmations', action='store_true', help='Проверить подтверждения консолидаций')

    def handle(self, *args, **options):
        if options['check_confirmations']:
            self.stdout.write("🔍 Проверка подтверждений консолидаций...")
            result = check_consolidation_confirmations()
            self.stdout.write(f"✅ {result}")
            return

        if options['dry_run']:
            self.stdout.write("🔍 Анализ возможных консолидаций (dry run)...")
            self.analyze_consolidations(options.get('currency'))
        else:
            self.stdout.write("🚀 Запуск консолидации депозитов...")
            if options.get('currency'):
                self.stdout.write(f"   Только для валюты: {options['currency']}")
            
            result = consolidate_user_deposits()
            self.stdout.write(f"✅ {result}")

    def analyze_consolidations(self, currency_filter=None):
        """Анализ возможных консолидаций без выполнения"""
        # Получаем все активные валюты без MEMO
        currencies_query = Cryptocurrency.objects.filter(
            is_active=True, 
            requires_memo=False
        )
        
        if currency_filter:
            currencies_query = currencies_query.filter(symbol__iexact=currency_filter)
        
        currencies = currencies_query.all()
        
        total_consolidations = 0
        total_amount = {}
        
        for currency in currencies:
            self.stdout.write(f"\n📊 Анализ {currency.symbol}:")
            
            # Получаем пользовательские кошельки с адресами
            user_wallets = UserWallet.objects.filter(
                currency=currency,
                is_system_wallet=False,
                deposit_address__isnull=False,
                encrypted_private_key__isnull=False
            ).exclude(deposit_address='')
            
            self.stdout.write(f"   Кошельков пользователей: {user_wallets.count()}")
            
            if user_wallets.count() == 0:
                continue
                
            # Проверяем системный кошелек
            try:
                system_wallet = UserWallet.objects.get(
                    user=None,
                    currency=currency,
                    is_system_wallet=True,
                    is_active=True
                )
                
                if not system_wallet.encrypted_private_key:
                    self.stdout.write(f"   ⚠️ Системный кошелек не имеет приватного ключа")
                    continue
                    
                self.stdout.write(f"   ✅ Системный кошелек настроен")
                
            except UserWallet.DoesNotExist:
                self.stdout.write(f"   ❌ Системный кошелек не найден")
                continue
            
            # Анализируем балансы (эмуляция проверки блокчейна)
            currency_consolidations = 0
            currency_amount = 0
            
            self.stdout.write(f"   👤 Анализ пользовательских кошельков:")
            
            for wallet in user_wallets[:5]:  # Показываем первые 5
                try:
                    from crypto.blockchain.factory import get_blockchain_service
                    from crypto.tasks_consolidation import get_min_consolidation_amount
                    
                    blockchain_service = get_blockchain_service(currency.network or currency.symbol)
                    balance = blockchain_service.get_balance(wallet.deposit_address)
                    min_amount = get_min_consolidation_amount(currency)
                    
                    if balance >= min_amount:
                        currency_consolidations += 1
                        currency_amount += float(balance)
                        self.stdout.write(f"      ✅ User {wallet.user_id}: {balance} {currency.symbol} (будет консолидирован)")
                    else:
                        self.stdout.write(f"      ℹ️ User {wallet.user_id}: {balance} {currency.symbol} (слишком мало)")
                        
                except Exception as e:
                    self.stdout.write(f"      ❌ User {wallet.user_id}: ошибка проверки баланса - {e}")
                    
            if user_wallets.count() > 5:
                self.stdout.write(f"      ... и еще {user_wallets.count() - 5} кошельков")
            
            total_consolidations += currency_consolidations
            total_amount[currency.symbol] = currency_amount
            
            self.stdout.write(f"   📦 Итого для {currency.symbol}: {currency_consolidations} консолидаций на {currency_amount:.6f} {currency.symbol}")
        
        self.stdout.write(f"\n📈 ОБЩИЙ ИТОГ:")
        self.stdout.write(f"   Всего консолидаций: {total_consolidations}")
        for symbol, amount in total_amount.items():
            if amount > 0:
                self.stdout.write(f"   {symbol}: {amount:.6f}")
                
        if total_consolidations == 0:
            self.stdout.write("   ℹ️ Нет депозитов для консолидации")
        else:
            self.stdout.write(f"\n💡 Для выполнения консолидации запустите без --dry-run")
