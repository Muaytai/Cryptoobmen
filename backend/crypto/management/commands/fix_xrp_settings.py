from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency
from decimal import Decimal

class Command(BaseCommand):
    help = "Исправляет настройки XRP для корректной работы вывода"

    def handle(self, *args, **options):
        self.stdout.write("=== Исправление настроек XRP ===\n")
        
        try:
            xrp_currency = Cryptocurrency.objects.get(symbol="XRP", network="XRP")
            
            # Проверяем и устанавливаем минимальные значения
            if xrp_currency.min_exchange_amount == Decimal('0.0001'):
                xrp_currency.min_exchange_amount = Decimal('1.0')  # Минимум 1 XRP
                self.stdout.write(self.style.SUCCESS("✅ Установлен min_exchange_amount: 1.0 XRP"))
            
            if xrp_currency.fee_percentage == Decimal('0.2'):
                xrp_currency.fee_percentage = Decimal('0.1')  # Комиссия 0.1%
                self.stdout.write(self.style.SUCCESS("✅ Установлен fee_percentage: 0.1%"))
            
            if xrp_currency.max_exchange_amount == Decimal('10.0'):
                xrp_currency.max_exchange_amount = Decimal('1000000.0')  # Максимум 1M XRP
                self.stdout.write(self.style.SUCCESS("✅ Установлен max_exchange_amount: 1,000,000 XRP"))
            
            xrp_currency.save()
            
            self.stdout.write(self.style.SUCCESS(f"✅ Настройки XRP обновлены:"))
            self.stdout.write(f"   - min_exchange_amount: {xrp_currency.min_exchange_amount}")
            self.stdout.write(f"   - fee_percentage: {xrp_currency.fee_percentage}%")
            self.stdout.write(f"   - max_exchange_amount: {xrp_currency.max_exchange_amount}")
            self.stdout.write(f"   - requires_memo: {xrp_currency.requires_memo}")
            
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ Криптовалюта XRP не найдена!"))
            return
        
        self.stdout.write("\n=== Настройки XRP исправлены ===") 