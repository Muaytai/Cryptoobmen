from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, SystemWalletAddress
from crypto.blockchain.bnb import BNBService

class Command(BaseCommand):
    help = "Настраивает BNB в тестовой сети BSC Testnet"

    def add_arguments(self, parser):
        parser.add_argument(
            '--network',
            type=str,
            default='testnet',
            choices=['testnet', 'mainnet'],
            help='Сеть BSC (testnet или mainnet)'
        )

    def handle(self, *args, **options):
        network = options['network']
        self.stdout.write(f"=== Настройка BNB в BSC {network} ===\n")
        
        try:
            # 1. Создаем/обновляем криптовалюту BNB
            bnb_currency, created = Cryptocurrency.objects.get_or_create(
                symbol="BNB",
                network="BSC_TESTNET",
                defaults={
                    'name': 'Binance Coin (Testnet)',
                    'currency_type': 'crypto',
                    'is_active': True,
                    'requires_memo': False,  # BSC не требует memo
                    'decimals': 18,
                    'coingecko_id': 'binancecoin',
                    'fee_percentage': 0.2,  # 0.2% комиссия
                    'min_exchange_amount': 0.001,
                    'max_exchange_amount': 100.0
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Создана криптовалюта BNB (BSC Testnet)"))
            else:
                self.stdout.write(self.style.SUCCESS(f"✅ Криптовалюта BNB (BSC Testnet) уже существует"))
            
            # 2. Создаем BSC сервис
            service = BNBService(network=network)
            
            # 3. Генерируем новый адрес
            address, private_key = service.create_new_address()
            self.stdout.write(f"✅ Сгенерирован новый BSC адрес: {address}")
            
            # 4. Сохраняем системный адрес
            system_address, created = SystemWalletAddress.objects.get_or_create(
                currency=bnb_currency,
                network="BSC_TESTNET",
                defaults={
                    'address': address
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Создан системный адрес BNB: {address}"))
            else:
                # Обновляем существующий адрес
                system_address.address = address
                system_address.save()
                self.stdout.write(self.style.SUCCESS(f"✅ Обновлен системный адрес BNB: {address}"))
            
            # 5. Создаем системный кошелек
            from crypto.models import UserWallet
            system_wallet, created = UserWallet.objects.get_or_create(
                currency=bnb_currency,
                is_system_wallet=True,
                defaults={
                    'balance': 0,
                    'available_balance': 0,
                    'locked_balance': 0,
                    'is_active': True,
                    'encrypted_private_key': private_key  # В продакшене нужно шифровать
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Создан системный кошелек BNB"))
            else:
                system_wallet.encrypted_private_key = private_key
                system_wallet.save()
                self.stdout.write(self.style.SUCCESS(f"✅ Обновлен системный кошелек BNB"))
            
            self.stdout.write(self.style.SUCCESS(f"\n�� BNB в BSC {network} успешно настроен!"))
            self.stdout.write(f"📝 Адрес для депозитов: {address}")
            self.stdout.write(f"🔑 Приватный ключ: {private_key}")
            self.stdout.write(f"⚠️  ВНИМАНИЕ: В продакшене приватный ключ должен быть зашифрован!")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка при настройке BNB: {e}"))
            raise