from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency

class Command(BaseCommand):
    help = "Исправляет настройки MEMO для XRP"

    def handle(self, *args, **options):
        self.stdout.write("=== Исправление настроек MEMO для XRP ===\n")
        
        try:
            xrp_currency = Cryptocurrency.objects.get(symbol="XRP", network="XRP")
            
            # Делаем MEMO обязательным для XRP (XRP Ledger требует MEMO)
            if not xrp_currency.requires_memo:
                xrp_currency.requires_memo = True
                xrp_currency.save()
                self.stdout.write(self.style.SUCCESS("✅ MEMO сделан обязательным для XRP"))
            else:
                self.stdout.write(self.style.WARNING("⚠️  MEMO уже обязателен для XRP"))
            
            self.stdout.write(self.style.SUCCESS(f"✅ Настройки XRP обновлены:"))
            self.stdout.write(f"   - requires_memo: {xrp_currency.requires_memo}")
            
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ Криптовалюта XRP не найдена!"))
            return
        
        self.stdout.write("\n=== Настройки MEMO исправлены ===") 