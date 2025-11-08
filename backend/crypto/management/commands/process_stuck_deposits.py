from django.core.management.base import BaseCommand
from crypto.tasks_consolidation import consolidate_user_deposits, check_consolidation_confirmations
from transactions.models import Transaction
from crypto.models import Cryptocurrency
from django.db.models import Q


class Command(BaseCommand):
    help = 'Обрабатывает зависшие pending депозиты через консолидацию'

    def add_arguments(self, parser):
        parser.add_argument('--check-confirmations', action='store_true', 
                          help='Проверить подтверждения консолидаций вместо запуска консолидации')

    def handle(self, *args, **options):
        # Показываем текущее состояние
        pending_deposits = Transaction.objects.filter(
            type='deposit',
            status='pending'
        )
        
        self.stdout.write(f"📊 Найдено зависших pending депозитов: {pending_deposits.count()}")
        
        if pending_deposits.count() > 0:
            # Группируем по валюте
            deposits_by_currency = {}
            for deposit in pending_deposits:
                symbol = deposit.crypto.symbol
                network = deposit.crypto.network or ''
                key = f"{symbol} ({network})"
                if key not in deposits_by_currency:
                    deposits_by_currency[key] = []
                deposits_by_currency[key].append(deposit)
            
            self.stdout.write("\n📋 Распределение по валютам:")
            for currency_key, deposits in deposits_by_currency.items():
                total_amount = sum(float(d.amount) for d in deposits)
                self.stdout.write(f"   {currency_key}: {len(deposits)} депозитов, сумма: {total_amount}")
        
        if options['check_confirmations']:
            self.stdout.write("\n🔍 Проверка подтверждений консолидаций...")
            result = check_consolidation_confirmations()
            self.stdout.write(self.style.SUCCESS(f"✅ {result}"))
        else:
            self.stdout.write("\n🚀 Запуск консолидации для обработки pending депозитов...")
            self.stdout.write("   (Это консолидирует средства с пользовательских адресов на системный кошелек)")
            
            try:
                result = consolidate_user_deposits()
                self.stdout.write(self.style.SUCCESS(f"✅ {result}"))
                
                # Показываем результат
                self.stdout.write("\n📊 Статус после консолидации:")
                pending_after = Transaction.objects.filter(type='deposit', status='pending').count()
                consolidation_txs = Transaction.objects.filter(type='consolidation', status='pending').count()
                
                self.stdout.write(f"   Pending депозитов: {pending_after}")
                self.stdout.write(f"   Pending консолидаций: {consolidation_txs}")
                
                if consolidation_txs > 0:
                    self.stdout.write("\n💡 Запустите с флагом --check-confirmations для проверки подтверждений консолидаций")
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Ошибка: {e}"))
                import traceback
                self.stdout.write(traceback.format_exc())

