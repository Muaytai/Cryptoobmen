from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, SystemWalletAddress

SYSTEM_ADDRESS = 'TMGXLnRtHjzdS9b4Ddoes95s6mmLvT9yrh'

class Command(BaseCommand):
    help = 'Создаёт недостающие системные кошельки для всех активных валют и сетей.'

    def handle(self, *args, **options):
        created = 0
        skipped = 0
        for currency in Cryptocurrency.objects.filter(is_active=True):
            if not SystemWalletAddress.objects.filter(currency=currency, network=currency.network).exists():
                SystemWalletAddress.objects.create(
                    currency=currency,
                    network=currency.network,
                    address=SYSTEM_ADDRESS
                )
                self.stdout.write(self.style.SUCCESS(f'Создан системный кошелёк для {currency.symbol} ({currency.network})'))
                created += 1
            else:
                skipped += 1
        self.stdout.write(self.style.SUCCESS(f'Готово! Создано: {created}, пропущено (уже есть): {skipped}')) 