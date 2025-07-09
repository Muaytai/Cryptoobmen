from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from crypto.models import Cryptocurrency, UserWallet

class Command(BaseCommand):
    help = 'Генерирует уникальные адреса для пополнения для всех пользователей и валют без MEMO/tag.'

    def handle(self, *args, **options):
        User = get_user_model()
        users = User.objects.all()
        currencies = Cryptocurrency.objects.filter(is_active=True, requires_memo=False)
        created = 0
        updated = 0
        for user in users:
            for currency in currencies:
                wallet, is_created = UserWallet.objects.get_or_create(
                    user=user,
                    currency=currency,
                    is_system_wallet=False,
                    defaults={}
                )
                test_address = f"TEST_{user.id}_{currency.symbol}_{currency.network or 'main'}"
                if wallet.deposit_address != test_address:
                    wallet.deposit_address = test_address
                    wallet.save()
                    if is_created:
                        created += 1
                    else:
                        updated += 1
        self.stdout.write(self.style.SUCCESS(f'Готово! Создано: {created}, обновлено: {updated}')) 