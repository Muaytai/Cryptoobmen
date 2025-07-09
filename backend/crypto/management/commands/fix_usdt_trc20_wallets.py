from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from crypto.models import UserWallet, Cryptocurrency
from django.db import transaction

ADDRESS = "TMGXLnRtHjzdS9b4Ddoes95s6mmLvT9yrh"
SYMBOL = "USDT"
NETWORK = "TRC20"

class Command(BaseCommand):
    help = "Жёстко пересоздаёт UserWallet по USDT (TRC20) с нужным адресом для всех пользователей."

    def handle(self, *args, **options):
        User = get_user_model()
        try:
            currency = Cryptocurrency.objects.get(symbol=SYMBOL, network=NETWORK)
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Cryptocurrency {SYMBOL} {NETWORK} не найдена!"))
            return

        users = User.objects.all()
        created = 0
        deleted = 0
        with transaction.atomic():
            for user in users:
                wallets = UserWallet.objects.filter(user=user, currency=currency, is_system_wallet=False)
                count = wallets.count()
                wallets.delete()
                deleted += count
                UserWallet.objects.create(
                    user=user,
                    currency=currency,
                    deposit_address=ADDRESS,
                    is_system_wallet=False
                )
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Готово! Создано: {created}, удалено старых: {deleted}")) 