from django.core.management.base import BaseCommand
from django.conf import settings
from crypto.models import Cryptocurrency, SystemWalletAddress, UserWallet
from crypto.blockchain.bitcoin import BitcoinService
from bip_utils import Bip44, Bip44Coins, Bip44Changes
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Настраивает системный адрес Bitcoin для депозитов и вывода"

    def add_arguments(self, parser):
        parser.add_argument(
            '--network',
            type=str,
            default='mainnet',
            choices=['testnet', 'mainnet'],
            help='Сеть Bitcoin (testnet или mainnet)'
        )
        parser.add_argument(
            '--index',
            type=int,
            default=0,
            help='Индекс для HD-кошелька (по умолчанию 0 для системного адреса)'
        )

    def handle(self, *args, **options):
        network = options['network']
        system_index = options['index']
        
        self.stdout.write(f"=== Настройка системного адреса Bitcoin ({network}) ===\n")
        
        try:
            # 1. Проверяем наличие BITCOIN_MASTER_SEED_HEX
            master_seed_hex = getattr(settings, 'BITCOIN_MASTER_SEED_HEX', None)
            if not master_seed_hex:
                self.stdout.write(
                    self.style.ERROR(
                        "❌ BITCOIN_MASTER_SEED_HEX не настроен в settings!\n"
                        "Добавьте BITCOIN_MASTER_SEED_HEX в .env.backend или settings.py"
                    )
                )
                return
            
            # 2. Проверяем/создаем криптовалюту BTC
            btc_currency, created = Cryptocurrency.objects.get_or_create(
                symbol="BTC",
                network="BTC",
                defaults={
                    'name': 'Bitcoin',
                    'currency_type': 'crypto',
                    'is_active': True,
                    'requires_memo': False,
                    'decimals': 8,
                    'coingecko_id': 'bitcoin'
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Создана криптовалюта BTC"))
            else:
                self.stdout.write(self.style.SUCCESS(f"✅ Криптовалюта BTC уже существует"))
            
            # 3. Создаем Bitcoin сервис
            service = BitcoinService(network=network)
            
            # 4. Генерируем системный адрес с фиксированным индексом
            self.stdout.write(f"Генерация системного адреса с индексом {system_index}...")
            
            try:
                seed_bytes = bytes.fromhex(master_seed_hex)
                bip44_mst = Bip44.FromSeed(seed_bytes, service.bip44_coin)
                
                # Путь для системного адреса: m/44'/<coin_type>'/0'/0/<system_index>
                # Используем фиксированный индекс для системного кошелька
                bip44_acc = bip44_mst.Purpose().Coin().Account(0)
                bip44_chg = bip44_acc.Change(Bip44Changes.CHAIN_EXT)
                bip44_addr = bip44_chg.AddressIndex(system_index)
                
                address = bip44_addr.PublicKey().ToAddress()
                private_key_wif = bip44_addr.PrivateKey().ToWif()
                
                self.stdout.write(self.style.SUCCESS(f"✅ Сгенерирован системный Bitcoin адрес: {address}"))
                self.stdout.write(f"   - Индекс: {system_index}")
                self.stdout.write(f"   - Сеть: {network}")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Ошибка генерации адреса: {e}")
                )
                logger.exception("Error generating Bitcoin system address")
                return
            
            # 5. Сохраняем системный адрес в SystemWalletAddress
            system_address, created = SystemWalletAddress.objects.get_or_create(
                currency=btc_currency,
                network="BTC",
                defaults={
                    'address': address
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Создан системный адрес BTC в SystemWalletAddress"))
            else:
                # Обновляем существующий адрес
                old_address = system_address.address
                system_address.address = address
                system_address.save()
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  Обновлен системный адрес BTC: {old_address} -> {address}"
                    )
                )
            
            self.stdout.write(f"   - Адрес в SystemWalletAddress: {system_address.address}")
            self.stdout.write(f"   - Сеть: {system_address.network}")
            self.stdout.write(f"   - Валюта: {system_address.currency.symbol}")

            # 6. Обновляем/создаем системный кошелек для вывода (UserWallet)
            system_wallet, wallet_created = UserWallet.objects.get_or_create(
                user=None,
                currency=btc_currency,
                is_system_wallet=True,
                defaults={
                    'balance': 0,
                    'available_balance': 0,
                    'locked_balance': 0,
                }
            )

            old_wallet_address = system_wallet.deposit_address
            system_wallet.deposit_address = address
            system_wallet.encrypted_private_key = private_key_wif
            system_wallet.save(update_fields=['deposit_address', 'encrypted_private_key'])

            if wallet_created:
                self.stdout.write(self.style.SUCCESS("✅ Создан системный кошелек BTC для вывода (UserWallet)"))
            else:
                if old_wallet_address != address:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️  Обновлен системный кошелек BTC: {old_wallet_address} -> {address}"
                        )
                    )
                else:
                    self.stdout.write(self.style.SUCCESS("✅ Системный кошелек BTC уже настроен"))
            
            # 7. Проверяем баланс
            try:
                balance = service.get_balance(address)
                self.stdout.write(f"   - Баланс: {balance} BTC")
                if balance > 0:
                    self.stdout.write(self.style.SUCCESS(f"   ✅ На адресе есть средства: {balance} BTC"))
                else:
                    self.stdout.write(self.style.WARNING(f"   ⚠️  Адрес пустой (баланс: 0 BTC)"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠️  Не удалось получить баланс: {e}"))
            
            self.stdout.write(self.style.SUCCESS(f"\n✅ Системный адрес Bitcoin настроен успешно!"))
            self.stdout.write(f"\n📝 Важно:")
            self.stdout.write(f"   - Приватный ключ сохранен в UserWallet.encrypted_private_key")
            self.stdout.write(f"   - Адрес сохранен в SystemWalletAddress и UserWallet")
            self.stdout.write(f"   - Индекс HD-кошелька: {system_index}")
            self.stdout.write(f"   - Путь: m/44'/{service.bip44_coin.value}'/0'/0/{system_index}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка настройки Bitcoin: {e}"))
            logger.exception("Error setting up Bitcoin system address")
            raise
