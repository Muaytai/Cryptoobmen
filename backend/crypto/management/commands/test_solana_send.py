from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, UserWallet
from crypto.blockchain.factory import get_blockchain_service
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Тестирует отправку Solana транзакции'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to-address',
            type=str,
            required=True,
            help='Адрес получателя для тестовой транзакции',
        )
        parser.add_argument(
            '--amount',
            type=str,
            default='0.001',
            help='Сумма для отправки (по умолчанию: 0.001 SOL)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Только проверка без отправки транзакции',
        )

    def handle(self, *args, **options):
        self.stdout.write("=== Тест отправки Solana ===\n")
        
        try:
            # Находим SOL валюту
            try:
                sol_currency = Cryptocurrency.objects.get(symbol__iexact='SOL', is_active=True)
                self.stdout.write(f"✓ Валюта найдена: {sol_currency}")
            except Cryptocurrency.DoesNotExist:
                self.stdout.write(self.style.ERROR("✗ SOL валюта не найдена"))
                return

            # Находим системный кошелёк
            try:
                system_wallet = UserWallet.objects.get(
                    currency=sol_currency,
                    is_system_wallet=True,
                    is_active=True
                )
                self.stdout.write(f"✓ Системный кошелёк найден: баланс {system_wallet.balance} SOL")
            except UserWallet.DoesNotExist:
                self.stdout.write(self.style.ERROR("✗ Системный кошелёк не найден"))
                return

            if not system_wallet.encrypted_private_key:
                self.stdout.write(self.style.ERROR("✗ Приватный ключ не установлен"))
                return

            # Парсим параметры
            to_address = options['to_address']
            amount = Decimal(options['amount'])
            
            self.stdout.write(f"Получатель: {to_address}")
            self.stdout.write(f"Сумма: {amount} SOL")

            # Получаем блокчейн сервис
            try:
                service = get_blockchain_service(sol_currency.network)
                self.stdout.write(f"✓ Сервис инициализирован: {service.__class__.__name__}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Ошибка инициализации сервиса: {e}"))
                return

            # Валидируем адрес получателя
            if not service.validate_address(to_address):
                self.stdout.write(self.style.ERROR(f"✗ Неверный адрес получателя: {to_address}"))
                return
            self.stdout.write(f"✓ Адрес получателя корректен")

            # Проверяем приватный ключ
            try:
                key_bytes = service._parse_private_key(system_wallet.encrypted_private_key)
                from solders.keypair import Keypair
                keypair = Keypair.from_bytes(key_bytes)
                sender_address = str(keypair.pubkey())
                self.stdout.write(f"✓ Приватный ключ корректен")
                self.stdout.write(f"  Адрес отправителя: {sender_address}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Ошибка парсинга приватного ключа: {e}"))
                return

            # Проверяем баланс в блокчейне
            try:
                blockchain_balance = service.get_balance(sender_address)
                self.stdout.write(f"✓ Баланс в блокчейне: {blockchain_balance} SOL")
                
                min_needed = amount + Decimal('0.01')  # запас на комиссии
                if blockchain_balance < min_needed:
                    self.stdout.write(self.style.ERROR(
                        f"✗ Недостаточно средств! Нужно: {min_needed} SOL, доступно: {blockchain_balance} SOL"
                    ))
                    return
                    
                self.stdout.write(f"✓ Средств достаточно")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Ошибка получения баланса: {e}"))
                return

            if options['dry_run']:
                self.stdout.write(f"\n✓ Тест завершён успешно (dry-run)")
                self.stdout.write(f"Транзакция не была отправлена")
                return

            # Отправляем тестовую транзакцию
            self.stdout.write(f"\n--- Отправка транзакции ---")
            try:
                tx_hash = service.send_transaction(
                    system_wallet.encrypted_private_key,
                    to_address,
                    amount,
                    f"test_transaction_solana"
                )
                
                self.stdout.write(self.style.SUCCESS(f"✓ Транзакция отправлена успешно!"))
                self.stdout.write(f"  Hash: {tx_hash}")
                self.stdout.write(f"  Explorer: https://explorer.solana.com/tx/{tx_hash}?cluster=devnet")
                
                # Обновляем баланс системного кошелька
                system_wallet.balance -= amount
                system_wallet.available_balance -= amount
                system_wallet.save()
                self.stdout.write(f"✓ Баланс системного кошелька обновлён: {system_wallet.balance} SOL")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Ошибка отправки транзакции: {e}"))
                logger.exception("Ошибка отправки тестовой транзакции")
                return

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Критическая ошибка: {e}"))
            logger.exception("Критическая ошибка в test_solana_send")

        self.stdout.write("\n=== Тест завершён ===")