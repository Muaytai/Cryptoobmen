from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, UserWallet
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Исправляет распространённые проблемы с Solana кошельком'

    def add_arguments(self, parser):
        parser.add_argument(
            '--private-key',
            type=str,
            help='Приватный ключ для системного кошелька (hex, JSON массив или base58)',
        )
        parser.add_argument(
            '--add-balance',
            type=str,
            help='Добавить баланс к системному кошельку (например: 1.5)',
        )

    def handle(self, *args, **options):
        self.stdout.write("=== Исправление проблем Solana ===\n")
        
        try:
            # Находим или создаём криптовалюту SOL
            sol_currency, created = Cryptocurrency.objects.get_or_create(
                symbol='SOL',
                defaults={
                    'name': 'Solana',
                    'network': 'solana',
                    'decimals': 9,
                    'is_active': True,
                    'min_exchange_amount': Decimal('0.01'),
                    'fee_percentage': Decimal('0.1'),
                    'requires_memo': False,
                }
            )
            
            if created:
                self.stdout.write(f"✓ Создана новая валюта: {sol_currency}")
            else:
                self.stdout.write(f"✓ Найдена валюта: {sol_currency}")

            # Находим или создаём системный кошелёк
            system_wallet, created = UserWallet.objects.get_or_create(
                currency=sol_currency,
                is_system_wallet=True,
                defaults={
                    'user': None,
                    'balance': Decimal('0'),
                    'available_balance': Decimal('0'),
                    'locked_balance': Decimal('0'),
                    'is_active': True,
                }
            )
            
            if created:
                self.stdout.write(f"✓ Создан новый системный кошелёк: {system_wallet}")
            else:
                self.stdout.write(f"✓ Найден системный кошелёк: {system_wallet}")

            # Устанавливаем приватный ключ, если предоставлен
            if options['private_key']:
                private_key = options['private_key'].strip()
                
                # Валидируем приватный ключ
                try:
                    from crypto.blockchain.factory import get_blockchain_service
                    service = get_blockchain_service('solana')
                    key_bytes = service._parse_private_key(private_key)
                    
                    # Получаем адрес кошелька
                    from solders.keypair import Keypair
                    keypair = Keypair.from_bytes(key_bytes)
                    wallet_address = str(keypair.pubkey())
                    
                    system_wallet.encrypted_private_key = private_key
                    system_wallet.save()
                    
                    self.stdout.write(f"✓ Приватный ключ установлен")
                    self.stdout.write(f"  Адрес кошелька: {wallet_address}")
                    
                    # Проверяем баланс в блокчейне
                    try:
                        blockchain_balance = service.get_balance(wallet_address)
                        self.stdout.write(f"  Баланс в блокчейне: {blockchain_balance} SOL")
                        
                        # Синхронизируем баланс, если он отличается
                        if blockchain_balance != system_wallet.balance:
                            system_wallet.balance = blockchain_balance
                            system_wallet.available_balance = blockchain_balance
                            system_wallet.save()
                            self.stdout.write(f"✓ Баланс синхронизирован: {blockchain_balance} SOL")
                            
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"⚠ Не удалось получить баланс из блокчейна: {e}"))
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ Неверный приватный ключ: {e}"))
                    return

            # Добавляем баланс, если указано
            if options['add_balance']:
                try:
                    additional_balance = Decimal(options['add_balance'])
                    system_wallet.balance += additional_balance
                    system_wallet.available_balance += additional_balance
                    system_wallet.save()
                    
                    self.stdout.write(f"✓ Добавлено {additional_balance} SOL к балансу")
                    self.stdout.write(f"  Новый баланс: {system_wallet.balance} SOL")
                except (ValueError, TypeError) as e:
                    self.stdout.write(self.style.ERROR(f"✗ Неверная сумма: {e}"))

            # Показываем текущее состояние
            self.stdout.write(f"\n--- Текущее состояние ---")
            self.stdout.write(f"Валюта: {sol_currency.name} ({sol_currency.symbol})")
            self.stdout.write(f"Сеть: {sol_currency.network}")
            self.stdout.write(f"Активна: {sol_currency.is_active}")
            self.stdout.write(f"Минимальная сумма: {sol_currency.min_exchange_amount}")
            self.stdout.write(f"Комиссия: {sol_currency.fee_percentage}%")
            self.stdout.write(f"Требует MEMO: {sol_currency.requires_memo}")
            self.stdout.write()
            self.stdout.write(f"Системный кошелёк ID: {system_wallet.id}")
            self.stdout.write(f"Баланс: {system_wallet.balance} SOL")
            self.stdout.write(f"Доступный баланс: {system_wallet.available_balance} SOL")
            self.stdout.write(f"Приватный ключ установлен: {'Да' if system_wallet.encrypted_private_key else 'Нет'}")
            self.stdout.write(f"Активен: {system_wallet.is_active}")

            # Проверяем ожидающие транзакции
            from transactions.models import Withdrawal
            pending_count = Withdrawal.objects.filter(
                wallet__currency=sol_currency,
                transaction__status__in=['pending', 'processing']
            ).count()
            
            if pending_count > 0:
                self.stdout.write(f"\n⚠ Ожидающих выводов: {pending_count}")
                self.stdout.write("Для обработки ожидающих выводов выполните:")
                self.stdout.write("python manage.py shell -c \"from crypto.tasks import process_pending_withdrawals; process_pending_withdrawals()\"")
            else:
                self.stdout.write(f"\n✓ Нет ожидающих выводов")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Критическая ошибка: {e}"))
            logger.exception("Ошибка в fix_solana_issues")

        self.stdout.write("\n=== Исправление завершено ===")

        # Инструкции по дальнейшим действиям
        self.stdout.write("\n--- Инструкции ---")
        if not system_wallet.encrypted_private_key:
            self.stdout.write("1. Установите приватный ключ:")
            self.stdout.write("   python manage.py fix_solana_issues --private-key=\"ВАШ_ПРИВАТНЫЙ_КЛЮЧ\"")
            
        if system_wallet.balance <= Decimal('0.01'):
            self.stdout.write("2. Пополните системный кошелёк:")
            self.stdout.write("   - Отправьте SOL на адрес кошелька")
            self.stdout.write("   - Или добавьте баланс вручную для тестирования:")
            self.stdout.write("     python manage.py fix_solana_issues --add-balance=\"1.0\"")
            
        self.stdout.write("3. Проверьте состояние:")
        self.stdout.write("   python manage.py check_solana_system_wallet")