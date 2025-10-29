from django.core.management.base import BaseCommand
from crypto.models import UserWallet, Cryptocurrency
from crypto.blockchain.factory import get_blockchain_service

class Command(BaseCommand):
    help = "Обновляет адрес пользователя для USDT TRC-20"

    def handle(self, *args, **options):
        try:
            # Получаем пользователя и валюту
            usdt_trc20 = Cryptocurrency.objects.get(symbol='USDT', network='TRC20')
            user_wallet = UserWallet.objects.get(user_id=2, currency=usdt_trc20)

            self.stdout.write(f'Текущий адрес: {user_wallet.deposit_address}')

            # Создаем новый адрес
            service = get_blockchain_service('TRC20')
            new_address, private_key = service.create_new_address(user_id=2)

            self.stdout.write(f'Новый адрес: {new_address}')

            # Обновляем адрес в базе
            user_wallet.deposit_address = new_address
            user_wallet.encrypted_private_key = private_key
            user_wallet.save()

            self.stdout.write(self.style.SUCCESS('Адрес обновлен в базе данных'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {e}'))
