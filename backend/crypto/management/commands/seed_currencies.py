from django.core.management.base import BaseCommand
from django.db import transaction
from crypto.models import Cryptocurrency, UserWallet

CURRENCIES_DATA = [
    {
        "name": "Bitcoin", "symbol": "BTC", "currency_type": "crypto",
        "network": "Bitcoin", "coingecko_id": "bitcoin", "is_active": True
    },
    {
        "name": "Ethereum", "symbol": "ETH", "currency_type": "crypto",
        "network": "ERC-20", "coingecko_id": "ethereum", "is_active": True
    },
    {
        "name": "Tether", "symbol": "USDT", "currency_type": "crypto",
        "network": "TRC-20", "coingecko_id": "tether", "is_active": True
    },
]

class Command(BaseCommand):
    help = 'Seeds the database with initial currencies and system wallets.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Starting to seed currencies and system wallets...")

        for data in CURRENCIES_DATA:
            currency, created = Cryptocurrency.objects.get_or_create(
                symbol=data["symbol"],
                defaults={
                    "name": data["name"],
                    "currency_type": data["currency_type"],
                    "network": data["network"],
                    "coingecko_id": data["coingecko_id"],
                    "is_active": data["is_active"]
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created currency: {currency.symbol}'))
            else:
                # Optionally update if exists, or just report
                # currency.name = data["name"] # Example update
                # currency.save()
                self.stdout.write(self.style.WARNING(f'Currency {currency.symbol} already exists. Skipping creation, ensure details are correct.'))

            # Create system wallet for this currency
            system_wallet, sw_created = UserWallet.objects.get_or_create(
                currency=currency,
                is_system_wallet=True,
                defaults={'balance': 0, 'available_balance': 0} # Системные кошельки могут иметь начальный баланс, если нужно
            )
            if sw_created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created system wallet for: {currency.symbol}'))
            else:
                self.stdout.write(self.style.WARNING(f'System wallet for {currency.symbol} already exists.'))
        
        self.stdout.write(self.style.SUCCESS("Finished seeding currencies and system wallets.")) 