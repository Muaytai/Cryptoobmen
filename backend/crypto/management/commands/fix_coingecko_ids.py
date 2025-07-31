from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency

class Command(BaseCommand):
    help = "Исправляет coingecko_id для криптовалют"

    def handle(self, *args, **options):
        # Маппинг символов на coingecko_id
        coingecko_mapping = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'USDT': 'tether',
            'BNB': 'binancecoin',
            'XRP': 'ripple',
            'SOL': 'solana',
            'LTC': 'litecoin',
            'MATIC': 'matic-network',
        }

        updated_count = 0
        for crypto in Cryptocurrency.objects.all():
            if crypto.symbol in coingecko_mapping and not crypto.coingecko_id:
                crypto.coingecko_id = coingecko_mapping[crypto.symbol]
                crypto.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Обновлен {crypto.symbol} ({crypto.network}): coingecko_id={crypto.coingecko_id}')
                )
                updated_count += 1
            elif crypto.coingecko_id:
                self.stdout.write(
                    self.style.WARNING(f'Пропущен {crypto.symbol} ({crypto.network}): уже имеет coingecko_id={crypto.coingecko_id}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Не найден coingecko_id для {crypto.symbol} ({crypto.network})')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Обновлено {updated_count} криптовалют')
        ) 