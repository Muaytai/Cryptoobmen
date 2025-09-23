from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, UserWallet
from crypto.blockchain.factory import get_blockchain_service
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Проверяет состояние системного кошелька Solana'

    def handle(self, *args, **options):
        self.stdout.write("=== Проверка системного кошелька Solana ===\n")
        
        try:
            # Находим криптовалюту Solana
            try:
                sol_currency = Cryptocurrency.objects.get(symbol__iexact='SOL', is_active=True)
                self.stdout.write(f"✓ Найдена валюта: {sol_currency.name} ({sol_currency.symbol})")
                self.stdout.write(f"  Сеть: {sol_currency.network}")
                self.stdout.write(f"  Минимальная сумма обмена: {sol_currency.min_exchange_amount}")
                self.stdout.write(f"  Комиссия: {sol_currency.fee_percentage}%")
            except Cryptocurrency.DoesNotExist:
                self.stdout.write(self.style.ERROR("✗ Криптовалюта SOL не найдена или неактивна"))
                return

            # Находим системный кошелёк
            try:
                system_wallet = UserWallet.objects.get(
                    currency=sol_currency,
                    is_system_wallet=True,
                    is_active=True
                )
                self.stdout.write(f"✓ Найден системный кошелёк: ID={system_wallet.id}")
                self.stdout.write(f"  Баланс: {system_wallet.balance} SOL")
                self.stdout.write(f"  Доступный баланс: {system_wallet.available_balance} SOL")
                self.stdout.write(f"  Заблокированный баланс: {system_wallet.locked_balance} SOL")
            except UserWallet.DoesNotExist:
                self.stdout.write(self.style.ERROR("✗ Системный кошелёк SOL не найден"))
                self.stdout.write("Создание системного кошелька...")
                
                system_wallet = UserWallet.objects.create(
                    user=None,
                    currency=sol_currency,
                    balance=0,
                    is_system_wallet=True,
                    is_active=True
                )
                self.stdout.write(f"✓ Создан системный кошелёк: ID={system_wallet.id}")

            # Проверяем приватный ключ
            if system_wallet.encrypted_private_key:
                self.stdout.write("✓ Приватный ключ установлен")
                
                # Пробуем получить блокчейн сервис
                try:
                    service = get_blockchain_service(sol_currency.network)
                    self.stdout.write(f"✓ Сервис блокчейна инициализирован: {service.__class__.__name__}")
                    
                    # Пробуем парсить приватный ключ
                    try:
                        key_bytes = service._parse_private_key(system_wallet.encrypted_private_key)
                        self.stdout.write("✓ Приватный ключ корректен")
                        
                        # Получаем публичный адрес из приватного ключа
                        from solders.keypair import Keypair
                        keypair = Keypair.from_bytes(key_bytes)
                        wallet_address = str(keypair.pubkey())
                        self.stdout.write(f"  Адрес кошелька: {wallet_address}")
                        
                        # Проверяем баланс в блокчейне
                        try:
                            blockchain_balance = service.get_balance(wallet_address)
                            self.stdout.write(f"  Баланс в блокчейне: {blockchain_balance} SOL")
                            
                            if blockchain_balance != system_wallet.balance:
                                self.stdout.write(self.style.WARNING(
                                    f"⚠ Несоответствие балансов! База данных: {system_wallet.balance} SOL, "
                                    f"блокчейн: {blockchain_balance} SOL"
                                ))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"✗ Ошибка получения баланса: {e}"))
                            
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"✗ Ошибка парсинга приватного ключа: {e}"))
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ Ошибка инициализации блокчейн сервиса: {e}"))
            else:
                self.stdout.write(self.style.ERROR("✗ Приватный ключ не установлен"))
                self.stdout.write("Для решения проблемы:")
                self.stdout.write("1. Зайдите в админку Django")
                self.stdout.write("2. Найдите раздел 'Crypto' -> 'User wallets'")
                self.stdout.write(f"3. Отредактируйте системный кошелёк SOL (ID: {system_wallet.id})")
                self.stdout.write("4. Установите приватный ключ в поле 'Encrypted Private Key'")
                self.stdout.write("   Поддерживаемые форматы:")
                self.stdout.write("   - Hex (128 символов): abcd1234...")
                self.stdout.write("   - JSON массив: [251,34,123,...]")
                self.stdout.write("   - Base58 (редко)")

            # Проверяем активные заявки на вывод
            from transactions.models import Withdrawal
            pending_withdrawals = Withdrawal.objects.filter(
                wallet__currency=sol_currency,
                transaction__status__in=['pending', 'processing']
            ).count()
            
            if pending_withdrawals > 0:
                self.stdout.write(f"⚠ Найдено {pending_withdrawals} ожидающих заявок на вывод SOL")
            else:
                self.stdout.write("✓ Нет ожидающих заявок на вывод")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Критическая ошибка: {e}"))
            logger.exception("Ошибка в check_solana_system_wallet")

        self.stdout.write("\n=== Проверка завершена ===")