from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, SystemWalletAddress

class Command(BaseCommand):
    help = 'Создает системный адрес для BNB (BEP20)'

    def handle(self, *args, **options):
        # Адрес BNB кошелька
        bnb_address = "0xeA6BFd33720eCEBB96FB7FD1Bf5daCceF890Fa27"
        
        # Получаем или создаем валюту BNB
        bnb_currency, created = Cryptocurrency.objects.get_or_create(
            symbol='BNB',
            network='BEP20',
            defaults={
                'name': 'Binance Coin',
                'decimals': 18,
                'requires_memo': False,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Создана валюта BNB (BEP20)')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Валюта BNB (BEP20) уже существует')
            )
        
        # Создаем системный адрес
        system_wallet, created = SystemWalletAddress.objects.get_or_create(
            currency=bnb_currency,
            network='BEP20',
            defaults={
                'address': bnb_address
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Создан системный адрес BNB: {bnb_address}')
            )
        else:
            # Обновляем адрес, если он изменился
            if system_wallet.address != bnb_address:
                system_wallet.address = bnb_address
                system_wallet.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Обновлен системный адрес BNB: {bnb_address}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Системный адрес BNB уже существует: {bnb_address}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Настройка BNB завершена успешно!')
        )
