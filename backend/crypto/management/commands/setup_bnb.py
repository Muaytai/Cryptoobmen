from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, SystemWalletAddress
from crypto.blockchain.factory import get_blockchain_service
from decimal import Decimal

class Command(BaseCommand):
    help = 'Создает BNB валюту и системный кошелек для BSC сети'

    def handle(self, *args, **options):
        # Создаем или получаем BNB валюту
        bnb_currency, created = Cryptocurrency.objects.get_or_create(
            symbol='BNB',
            network='BEP20',
            defaults={
                'name': 'Binance Coin',
                'decimals': 18,
                'requires_memo': True,  # BNB требует memo для депозитов
                'is_active': True,
                'coingecko_id': 'binancecoin'
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Создана валюта BNB: {bnb_currency.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Валюта BNB уже существует: {bnb_currency.name}')
            )
        
        # Проверяем, есть ли системный кошелек для BNB
        system_wallet = SystemWalletAddress.objects.filter(
            currency=bnb_currency
        ).first()
        
        if not system_wallet:
            try:
                # Создаем новый адрес для BNB
                service = get_blockchain_service('BEP20')
                address, private_key = service.create_new_address()
                
                # Создаем системный кошелек
                system_wallet = SystemWalletAddress.objects.create(
                    currency=bnb_currency,
                    address=address,
                    encrypted_private_key=private_key,  # В реальном проекте нужно зашифровать
                    network='BEP20',
                    is_active=True
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Создан системный кошелек BNB: {address}')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Ошибка при создании системного кошелька BNB: {e}')
                )
        else:
            self.stdout.write(
                self.style.WARNING(f'Системный кошелек BNB уже существует: {system_wallet.address}')
            )
        
        # Показываем статистику
        self.stdout.write('\n=== Статистика BNB ===')
        self.stdout.write(f'Валюта: {bnb_currency.symbol} - {bnb_currency.network}')
        self.stdout.write(f'Активна: {bnb_currency.is_active}')
        self.stdout.write(f'Требует memo: {bnb_currency.requires_memo}')
        
        if system_wallet:
            self.stdout.write(f'Системный кошелек: {system_wallet.address}')
            self.stdout.write(f'Сеть: {system_wallet.network}')
            self.stdout.write(f'Активен: {system_wallet.is_active}')
