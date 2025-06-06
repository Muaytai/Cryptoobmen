from django.core.management.base import BaseCommand
from django.utils import timezone
from crypto.models import Cryptocurrency, CryptoPrice
from crypto.services import get_exchange_rates

class Command(BaseCommand):
    help = 'Fetches latest cryptocurrency prices from CoinGecko and updates the database.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting price update...'))
        
        active_cryptos = Cryptocurrency.objects.filter(is_active=True, currency_type='crypto').exclude(coingecko_id__isnull=True).exclude(coingecko_id__exact='')
        
        if not active_cryptos.exists():
            self.stdout.write(self.style.WARNING('No active cryptocurrencies with coingecko_id found. Nothing to update.'))
            return

        coingecko_ids = list(active_cryptos.values_list('coingecko_id', flat=True))
        
        self.stdout.write(f"Fetching prices for: {', '.join(coingecko_ids)}")
        
        try:
            rates = get_exchange_rates() # Эта функция уже должна быть в services.py
            if not rates:
                self.stdout.write(self.style.ERROR('Failed to fetch exchange rates. The service may be down or returned no data.'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred while fetching prices: {e}'))
            return
            
        updated_count = 0
        created_count = 0
        
        for crypto in active_cryptos:
            rate_data = rates.get(crypto.coingecko_id)
            if rate_data and 'usd' in rate_data:
                price_usd = rate_data['usd']
                
                # Создаем новую запись о цене
                CryptoPrice.objects.create(
                    crypto=crypto,
                    price_usd=price_usd,
                    timestamp=timezone.now()
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Successfully updated price for {crypto.symbol} to {price_usd} USD'))

        self.stdout.write(self.style.SUCCESS(f'Price update complete. Created {created_count} new price entries.')) 