from django.core.management.base import BaseCommand
from django.db import transaction
from crypto.models import Cryptocurrency, UserWallet
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """Обновляет системный кошелек XRP с правильным адресом."""

    help = "Обновить системный кошелек XRP с правильным адресом."

    def add_arguments(self, parser):
        parser.add_argument(
            "--address",
            type=str,
            required=True,
            help="Адрес системного кошелька XRP"
        )
        parser.add_argument(
            "--seed",
            type=str,
            required=True,
            help="Seed (приватный ключ) системного кошелька"
        )

    @transaction.atomic
    def handle(self, *args, **options):
        address = options.get("address")
        seed = options.get("seed")
        
        self.stdout.write(self.style.WARNING(f"Обновление системного кошелька XRP"))
        self.stdout.write(f"Адрес: {address}")
        
        # Находим криптовалюту XRP
        try:
            xrp_currency = Cryptocurrency.objects.get(symbol="XRP", network="XRP")
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(self.style.ERROR("Криптовалюта XRP не найдена в базе данных!"))
            return
        
        # Создаем или получаем системный кошелек
        system_wallet, created = UserWallet.objects.get_or_create(
            user=None,
            currency=xrp_currency,
            is_system_wallet=True,
            defaults={
                'balance': 0,
                'available_balance': 0,
                'is_active': True
            }
        )
        
        # Обновляем системный кошелек
        system_wallet.deposit_address = address
        system_wallet.encrypted_private_key = seed
        system_wallet.save()
        
        self.stdout.write(self.style.SUCCESS(
            f"Системный кошелек XRP обновлен успешно!\n"
            f"Адрес: {system_wallet.deposit_address}\n"
            f"Приватный ключ: {'Есть' if system_wallet.encrypted_private_key else 'Отсутствует'}\n"
            f"Статус: {'Создан' if created else 'Обновлен'}"
        )) 