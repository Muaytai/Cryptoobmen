from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from crypto.models import UserWallet, Cryptocurrency

ADDRESS = "TMGXLnRtHjzdS9b4Ddoes95s6mmLvT9yrh"
SYMBOL = "USDT"
NETWORK = "TRC20"

class Command(BaseCommand):
    help = "Обновляет UserWallet с нужным адресом так, чтобы currency указывал на USDT TRC20 (symbol=USDT, network=TRC20)"

    def handle(self, *args, **options):
        try:
            currency = Cryptocurrency.objects.get(symbol=SYMBOL, network=NETWORK)
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Cryptocurrency {SYMBOL} {NETWORK} не найдена!"))
            return

        wallets = UserWallet.objects.filter(deposit_address=ADDRESS)
        count = 0
        for wallet in wallets:
            if wallet.currency != currency:
                wallet.currency = currency
                wallet.save(update_fields=["currency"])
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Обновлено {count} UserWallet для {SYMBOL} {NETWORK}")) 