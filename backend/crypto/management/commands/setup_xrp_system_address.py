from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, SystemWalletAddress, UserWallet
from crypto.blockchain.xrp import XRPService

class Command(BaseCommand):
    help = "Настраивает системный адрес XRP для депозитов"

    def add_arguments(self, parser):
        parser.add_argument(
            '--network',
            type=str,
            default='testnet',
            choices=['testnet', 'mainnet'],
            help='Сеть XRP (testnet или mainnet)'
        )

    def handle(self, *args, **options):
        network = options['network']
        self.stdout.write(f"=== Настройка системного адреса XRP ({network}) ===\n")
        
        try:
            # 1. Проверяем/создаем криптовалюту XRP
            xrp_currency, created = Cryptocurrency.objects.get_or_create(
                symbol="XRP",
                network="XRP",
                defaults={
                    'name': 'Ripple',
                    'currency_type': 'crypto',
                    'is_active': True,
                    'requires_memo': True,
                    'decimals': 6,
                    'coingecko_id': 'ripple'
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Создана криптовалюта XRP"))
            else:
                self.stdout.write(self.style.SUCCESS(f"✅ Криптовалюта XRP уже существует"))
            
            # 2. Создаем XRP сервис
            service = XRPService(network=network)
            
            # 3. Генерируем новый адрес
            address, private_key = service.create_new_address()
            self.stdout.write(f"✅ Сгенерирован новый XRP адрес: {address}")
            
            # 4. Сохраняем системный адрес
            system_address, created = SystemWalletAddress.objects.get_or_create(
                currency=xrp_currency,
                network="XRP",
                defaults={
                    'address': address
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Создан системный адрес XRP"))
            else:
                # Обновляем существующий адрес
                system_address.address = address
                system_address.save()
                self.stdout.write(self.style.SUCCESS(f"✅ Обновлен системный адрес XRP"))
            
            self.stdout.write(f"   - Адрес: {system_address.address}")
            self.stdout.write(f"   - Сеть: {system_address.network}")
            self.stdout.write(f"   - Валюта: {system_address.currency.symbol}")

            # 5. Обновляем/создаем системный кошелек для вывода
            system_wallet, wallet_created = UserWallet.objects.get_or_create(
                user=None,
                currency=xrp_currency,
                is_system_wallet=True,
                defaults={
                    'balance': 0,
                    'available_balance': 0,
                    'locked_balance': 0,
                }
            )

            system_wallet.deposit_address = address
            system_wallet.encrypted_private_key = private_key
            system_wallet.save(update_fields=['deposit_address', 'encrypted_private_key'])

            if wallet_created:
                self.stdout.write(self.style.SUCCESS("✅ Создан системный кошелек XRP для вывода"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ Обновлен системный кошелек XRP для вывода"))
            
            # 6. Проверяем баланс
            try:
                balance = service.get_balance(address)
                self.stdout.write(f"   - Баланс: {balance} XRP")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠️  Не удалось получить баланс: {e}"))
            
            self.stdout.write(self.style.SUCCESS(f"\n✅ Системный адрес XRP настроен успешно!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка настройки XRP: {e}"))
            raise 