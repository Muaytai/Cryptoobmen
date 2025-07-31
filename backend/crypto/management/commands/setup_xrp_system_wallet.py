from django.core.management.base import BaseCommand
from django.db import transaction
from crypto.models import Cryptocurrency, UserWallet
from crypto.blockchain.xrp import XRPService
from xrpl.wallet import Wallet
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """Создаёт системный кошелек XRP с приватным ключом для вывода средств."""

    help = "Создать системный кошелек XRP с приватным ключом для вывода средств."

    def add_arguments(self, parser):
        parser.add_argument(
            "--network",
            type=str,
            choices=['testnet', 'mainnet'],
            default='testnet',
            help="Сеть XRP (testnet или mainnet)"
        )
        parser.add_argument(
            "--seed",
            type=str,
            help="Существующий seed для кошелька (опционально)"
        )

    @transaction.atomic
    def handle(self, *args, **options):
        network = options.get("network", "testnet")
        existing_seed = options.get("seed")
        
        self.stdout.write(self.style.WARNING(f"Настройка системного кошелька XRP для сети: {network}"))
        
        # Находим или создаем криптовалюту XRP
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
        
        if existing_seed:
            # Используем предоставленный seed
            wallet = Wallet.from_seed(existing_seed)
            self.stdout.write(self.style.SUCCESS(f"Используется предоставленный seed для адреса: {wallet.classic_address}"))
        else:
            # Создаем новый кошелек
            wallet = Wallet.create()
            self.stdout.write(self.style.SUCCESS(f"Создан новый кошелек XRP: {wallet.classic_address}"))
            self.stdout.write(self.style.WARNING(f"Seed: {wallet.seed}"))
            self.stdout.write(self.style.WARNING("ВАЖНО: Сохраните этот seed в безопасном месте!"))
        
        # Обновляем системный кошелек
        system_wallet.encrypted_private_key = wallet.seed
        system_wallet.save()
        
        # Проверяем баланс
        try:
            service = XRPService(network=network)
            balance = service.get_balance(wallet.classic_address)
            self.stdout.write(self.style.SUCCESS(f"Баланс системного кошелька: {balance} XRP"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Не удалось проверить баланс: {e}"))
        
        self.stdout.write(self.style.SUCCESS(
            f"Системный кошелек XRP настроен успешно!\n"
            f"Адрес: {wallet.classic_address}\n"
            f"Сеть: {network}\n"
            f"Статус: {'Создан' if created else 'Обновлен'}"
        )) 