from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, UserWallet
from crypto.blockchain.factory import get_blockchain_service
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Создает системные кошельки для всех активных криптовалют'

    def handle(self, *args, **options):
        self.stdout.write('=== СОЗДАНИЕ СИСТЕМНЫХ КОШЕЛЬКОВ ===')
        
        # Получаем все активные криптовалюты
        cryptocurrencies = Cryptocurrency.objects.filter(is_active=True, currency_type='crypto')
        
        for currency in cryptocurrencies:
            try:
                # Проверяем, есть ли уже системный кошелек для этой валюты
                system_wallet, created = UserWallet.objects.get_or_create(
                    user=None,
                    currency=currency,
                    is_system_wallet=True,
                    defaults={
                        'balance': 0,
                        'available_balance': 0,
                        'locked_balance': 0,
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Создан системный кошелек для {currency.symbol} ({currency.network})')
                    )
                    
                    # Генерируем адрес для системного кошелька, если его нет
                    if not system_wallet.deposit_address and currency.network.upper() in ['ERC20', 'ETHEREUM']:
                        try:
                            # Используем приватный ключ из настроек для Ethereum
                            if hasattr(settings, 'ETHEREUM_PLATFORM_PRIVATE_KEY'):
                                from eth_account import Account
                                account = Account.from_key(settings.ETHEREUM_PLATFORM_PRIVATE_KEY)
                                system_wallet.deposit_address = account.address
                                system_wallet.encrypted_private_key = settings.ETHEREUM_PLATFORM_PRIVATE_KEY
                                system_wallet.save()
                                self.stdout.write(
                                    self.style.SUCCESS(f'  Адрес: {system_wallet.deposit_address}')
                                )
                            else:
                                # Генерируем новый адрес через сервис
                                service = get_blockchain_service(currency.network)
                                address, private_key = service.create_new_address()
                                system_wallet.deposit_address = address
                                system_wallet.encrypted_private_key = private_key
                                system_wallet.save()
                                self.stdout.write(
                                    self.style.SUCCESS(f'  Адрес: {system_wallet.deposit_address}')
                                )
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(f'  Не удалось создать адрес: {e}')
                            )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'- Системный кошелек для {currency.symbol} ({currency.network}) уже существует')
                    )
                    if system_wallet.deposit_address:
                        self.stdout.write(f'  Адрес: {system_wallet.deposit_address}')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Ошибка при создании кошелька для {currency.symbol}: {e}')
                )
        
        self.stdout.write(self.style.SUCCESS('\n=== СОЗДАНИЕ ЗАВЕРШЕНО ==='))