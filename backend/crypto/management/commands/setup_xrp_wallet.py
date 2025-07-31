from django.core.management.base import BaseCommand
from crypto.models import UserWallet, Cryptocurrency
from crypto.blockchain.xrp import XRPService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Создает и активирует системный XRP кошелек'

    def handle(self, *args, **options):
        self.stdout.write('=== НАСТРОЙКА СИСТЕМНОГО XRP КОШЕЛЬКА ===')
        
        # Находим XRP валюту
        try:
            xrp_currency = Cryptocurrency.objects.get(symbol='XRP')
            self.stdout.write(f'✅ Найдена валюта XRP (ID: {xrp_currency.id})')
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ Валюта XRP не найдена в базе данных!'))
            return
        
        # Проверяем существующий системный кошелек
        existing_wallet = UserWallet.objects.filter(
            currency=xrp_currency,
            is_system_wallet=True
        ).first()
        
        if existing_wallet:
            self.stdout.write(f'Найден существующий системный кошелек:')
            self.stdout.write(f'  ID: {existing_wallet.id}')
            self.stdout.write(f'  Адрес: {existing_wallet.deposit_address}')
            self.stdout.write(f'  Баланс: {existing_wallet.balance}')
            self.stdout.write(f'  Приватный ключ: {"Есть" if existing_wallet.encrypted_private_key else "НЕТ!"}')
            
            if existing_wallet.encrypted_private_key:
                self.stdout.write('✅ Системный кошелек уже настроен!')
                return
            else:
                self.stdout.write('⚠️  Кошелек существует, но без приватного ключа. Создаем новый...')
        
        # Создаем новый системный кошелек
        try:
            self.stdout.write('Создаем новый системный XRP кошелек...')
            
            # Создаем кошелек без пользователя (системный)
            system_wallet = UserWallet.objects.create(
                user=None,  # Системный кошелек
                currency=xrp_currency,
                is_system_wallet=True,
                is_active=True,
                balance=0,
                available_balance=0,
                locked_balance=0
            )
            
            # Генерируем адрес и приватный ключ
            xrp_service = XRPService()
            address, private_key = xrp_service.create_new_address()
            
            # Сохраняем адрес и приватный ключ
            system_wallet.deposit_address = address
            system_wallet.encrypted_private_key = private_key
            system_wallet.save()
            
            self.stdout.write(f'✅ Системный XRP кошелек создан:')
            self.stdout.write(f'  ID: {system_wallet.id}')
            self.stdout.write(f'  Адрес: {address}')
            self.stdout.write(f'  Приватный ключ: Сохранен')
            
            self.stdout.write(self.style.SUCCESS('\n🎉 Системный XRP кошелек успешно создан!'))
            self.stdout.write('⚠️  ВАЖНО: Для работы выводов нужно пополнить этот кошелек минимум 20 XRP')
            self.stdout.write(f'   Адрес для пополнения: {address}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка при создании кошелька: {e}'))
            logger.error(f'Ошибка при создании системного XRP кошелька: {e}', exc_info=True) 