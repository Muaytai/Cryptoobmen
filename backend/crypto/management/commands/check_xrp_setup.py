from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, UserWallet
from crypto.blockchain.xrp import XRPService

class Command(BaseCommand):
    help = "Проверяет настройку XRP для вывода"

    def handle(self, *args, **options):
        self.stdout.write("=== Проверка настройки XRP ===\n")
        
        # 1. Проверяем криптовалюту XRP
        try:
            xrp_currency = Cryptocurrency.objects.get(symbol="XRP", network="XRP")
            self.stdout.write(self.style.SUCCESS(f"✅ Криптовалюта XRP найдена: {xrp_currency.name}"))
            self.stdout.write(f"   - coingecko_id: {xrp_currency.coingecko_id}")
            self.stdout.write(f"   - requires_memo: {getattr(xrp_currency, 'requires_memo', False)}")
            self.stdout.write(f"   - is_active: {xrp_currency.is_active}")
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ Криптовалюта XRP не найдена!"))
            return
        
        # 2. Проверяем системный кошелек XRP
        try:
            system_wallet = UserWallet.objects.get(
                user=None,
                currency=xrp_currency,
                is_system_wallet=True
            )
            self.stdout.write(self.style.SUCCESS(f"✅ Системный кошелек XRP найден"))
            self.stdout.write(f"   - Адрес: {system_wallet.deposit_address or 'Не установлен'}")
            self.stdout.write(f"   - Приватный ключ: {'Есть' if system_wallet.encrypted_private_key else 'Отсутствует'}")
            self.stdout.write(f"   - Баланс: {system_wallet.balance}")
            self.stdout.write(f"   - Активен: {system_wallet.is_active}")
            
            if not system_wallet.encrypted_private_key:
                self.stdout.write(self.style.WARNING("⚠️  Системный кошелек не имеет приватного ключа!"))
                self.stdout.write("   Запустите: python manage.py setup_xrp_system_wallet --network testnet")
                
        except UserWallet.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ Системный кошелек XRP не найден!"))
            self.stdout.write("   Запустите: python manage.py setup_xrp_system_wallet --network testnet")
            return
        
        # 3. Тестируем XRP сервис
        try:
            service = XRPService(network='testnet')
            self.stdout.write(self.style.SUCCESS("✅ XRP сервис создан успешно"))
            
            # Тестируем создание адреса
            address, private_key = service.create_new_address()
            self.stdout.write(f"   - Тестовый адрес: {address}")
            self.stdout.write(f"   - Приватный ключ: {private_key[:10]}...")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка создания XRP сервиса: {e}"))
        
        # 4. Проверяем цены
        try:
            from crypto.services import get_exchange_rates
            rates = get_exchange_rates()
            if rates and 'ripple' in rates:
                xrp_price = rates['ripple'].get('usd', 'N/A')
                self.stdout.write(self.style.SUCCESS(f"✅ Цена XRP: ${xrp_price}"))
            else:
                self.stdout.write(self.style.WARNING("⚠️  Цена XRP не найдена"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка получения цены XRP: {e}"))
        
        self.stdout.write("\n=== Проверка завершена ===") 