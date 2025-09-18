from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from crypto.models import Cryptocurrency, UserWallet
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Настраивает BNB кошелек для пользователя'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email пользователя')
        parser.add_argument('address', type=str, help='BNB адрес кошелька')

    def handle(self, *args, **options):
        email = options['email']
        address = options['address']
        
        self.stdout.write(f'Настройка BNB кошелька для {email}')
        self.stdout.write(f'Адрес: {address}')
        
        # Находим пользователя
        try:
            user = User.objects.get(email=email)
            self.stdout.write(f'Найден пользователь: {user.username} (ID: {user.id})')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Пользователь с email {email} не найден'))
            return
        
        # Находим BNB валюту
        try:
            bnb_currency = Cryptocurrency.objects.get(symbol='BNB', network='BEP20')
            self.stdout.write(f'Найдена валюта: {bnb_currency.name} ({bnb_currency.symbol})')
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(self.style.ERROR('BNB (BEP20) валюта не найдена'))
            self.stdout.write('Запустите: python manage.py seed_crypto_data')
            return
        
        # Создаем или обновляем кошелек пользователя
        user_wallet, created = UserWallet.objects.get_or_create(
            user=user,
            currency=bnb_currency,
            is_system_wallet=False,
            defaults={
                'balance': Decimal('0'),
                'available_balance': Decimal('0'),
                'locked_balance': Decimal('0'),
                'deposit_address': address,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Создан новый BNB кошелек для пользователя'))
        else:
            # Обновляем адрес если он отличается
            if user_wallet.deposit_address != address:
                old_address = user_wallet.deposit_address
                user_wallet.deposit_address = address
                user_wallet.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Обновлен адрес кошелька'))
                self.stdout.write(f'  Старый: {old_address}')
                self.stdout.write(f'  Новый: {address}')
            else:
                self.stdout.write(self.style.SUCCESS(f'✓ Кошелек уже существует с правильным адресом'))
        
        # Показываем текущее состояние
        self.stdout.write(f'\nТекущее состояние кошелька:')
        self.stdout.write(f'  Баланс: {user_wallet.balance} BNB')
        self.stdout.write(f'  Доступно: {user_wallet.available_balance} BNB')
        self.stdout.write(f'  Заблокировано: {user_wallet.locked_balance} BNB')
        self.stdout.write(f'  Адрес депозита: {user_wallet.deposit_address}')
        self.stdout.write(f'  Активен: {user_wallet.is_active}')
        
        self.stdout.write(f'\nТеперь система будет сканировать транзакции для адреса {address}')
        self.stdout.write('Убедитесь что:')
        self.stdout.write('1. Настроен BSCSCAN_API_KEY в .env файле')
        self.stdout.write('2. Запущена Celery задача check_blockchain_deposits')
        self.stdout.write('3. Или запустите ручное сканирование:')
        self.stdout.write(f'   python manage.py manual_scan_bnb {address} --user-id {user.id} --save')

