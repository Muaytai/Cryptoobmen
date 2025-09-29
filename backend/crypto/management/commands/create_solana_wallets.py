from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from crypto.models import Cryptocurrency, UserWallet
from crypto.blockchain.factory import get_blockchain_service
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Создает тестовые депозитные адреса Solana для пользователей'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email конкретного пользователя для создания кошелька',
        )
        parser.add_argument(
            '--add-test-balance',
            type=str,
            help='Добавить тестовый баланс в БД (например: 0.05)',
        )
        parser.add_argument(
            '--regenerate',
            action='store_true',
            help='Пересоздать адреса для кошельков, у которых они уже есть',
        )

    def handle(self, *args, **options):
        self.stdout.write("=== Создание Solana кошельков для пользователей ===\n")
        
        try:
            # Находим Solana валюту
            sol_currency = Cryptocurrency.objects.get(symbol__iexact='SOL', is_active=True)
            self.stdout.write(f"✓ Найдена валюта: {sol_currency.name} ({sol_currency.symbol})")
            
            # Получаем блокчейн сервис
            service = get_blockchain_service(sol_currency.network or sol_currency.symbol)
            self.stdout.write(f"✓ Блокчейн сервис: {service.__class__.__name__}")
            
            # Определяем пользователей для обработки
            if options.get('user_email'):
                try:
                    users = [User.objects.get(email=options['user_email'])]
                    self.stdout.write(f"Обработка пользователя: {options['user_email']}")
                except User.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Пользователь с email {options['user_email']} не найден"))
                    return
            else:
                users = User.objects.all()
                self.stdout.write(f"Обработка всех пользователей: {users.count()}")
            
            created_count = 0
            updated_count = 0
            skipped_count = 0
            
            for user in users:
                self.stdout.write(f"\n👤 Пользователь: {user.email} (ID: {user.id})")
                
                try:
                    # Получаем или создаем кошелек
                    wallet, created = UserWallet.objects.get_or_create(
                        user=user,
                        currency=sol_currency,
                        is_system_wallet=False,
                        defaults={
                            'balance': Decimal('0'),
                            'available_balance': Decimal('0'),
                            'locked_balance': Decimal('0'),
                            'is_active': True,
                        }
                    )
                    
                    if created:
                        self.stdout.write(f"  ✓ Создан новый кошелек: ID={wallet.id}")
                        created_count += 1
                    else:
                        self.stdout.write(f"  ✓ Найден кошелек: ID={wallet.id}")
                    
                    # Проверяем нужно ли создавать/обновлять адрес
                    need_address = False
                    
                    if not wallet.deposit_address:
                        need_address = True
                        self.stdout.write(f"  📍 Адрес отсутствует, создаем новый")
                    elif options.get('regenerate'):
                        need_address = True
                        self.stdout.write(f"  🔄 Пересоздание адреса (--regenerate)")
                    else:
                        self.stdout.write(f"  📍 Адрес уже есть: {wallet.deposit_address}")
                    
                    if need_address:
                        try:
                            # Создаем новый адрес
                            new_address, private_key = service.create_new_address(user_id=user.id)
                            
                            old_address = wallet.deposit_address
                            wallet.deposit_address = new_address
                            wallet.encrypted_private_key = private_key
                            wallet.save()
                            
                            if old_address:
                                self.stdout.write(f"  ✅ Адрес обновлен: {old_address} → {new_address}")
                                updated_count += 1
                            else:
                                self.stdout.write(f"  ✅ Создан адрес: {new_address}")
                                if not created:  # Кошелек был, но адреса не было
                                    updated_count += 1
                            
                            # Проверяем баланс в блокчейне
                            try:
                                blockchain_balance = service.get_balance(new_address)
                                self.stdout.write(f"  💰 Баланс в блокчейне: {blockchain_balance} SOL")
                            except Exception as e:
                                self.stdout.write(f"  ⚠ Ошибка проверки баланса: {e}")
                            
                        except Exception as e:
                            self.stdout.write(f"  ✗ Ошибка создания адреса: {e}")
                            continue
                    else:
                        skipped_count += 1
                    
                    # Добавляем тестовый баланс если запрошено
                    if options.get('add_test_balance'):
                        try:
                            test_balance = Decimal(options['add_test_balance'])
                            old_balance = wallet.balance
                            wallet.balance += test_balance
                            wallet.available_balance = wallet.balance - wallet.locked_balance
                            wallet.save()
                            
                            self.stdout.write(f"  💵 Баланс в БД: {old_balance} → {wallet.balance} SOL")
                        except (ValueError, TypeError) as e:
                            self.stdout.write(f"  ✗ Ошибка добавления баланса: {e}")
                    else:
                        self.stdout.write(f"  💵 Текущий баланс в БД: {wallet.balance} SOL")
                    
                except Exception as e:
                    self.stdout.write(f"  ✗ Ошибка обработки пользователя: {e}")
                    logger.exception(f"Ошибка при обработке пользователя {user.id}")
                    continue
            
            # Итоги
            self.stdout.write(f"\n--- ИТОГИ ---")
            self.stdout.write(f"Новых кошельков создано: {created_count}")
            self.stdout.write(f"Кошельков обновлено: {updated_count}")
            self.stdout.write(f"Кошельков пропущено: {skipped_count}")
            
            # Общая статистика
            total_wallets = UserWallet.objects.filter(
                currency=sol_currency,
                is_system_wallet=False
            ).count()
            
            wallets_with_addresses = UserWallet.objects.filter(
                currency=sol_currency,
                is_system_wallet=False,
                deposit_address__isnull=False
            ).exclude(deposit_address='').count()
            
            self.stdout.write(f"\nОбщая статистика Solana:")
            self.stdout.write(f"Всего пользовательских кошельков: {total_wallets}")
            self.stdout.write(f"Кошельков с адресами: {wallets_with_addresses}")
            
            if total_wallets > 0:
                coverage = (wallets_with_addresses / total_wallets) * 100
                self.stdout.write(f"Покрытие адресами: {coverage:.1f}%")
            
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(self.style.ERROR("✗ Валюта SOL не найдена!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Критическая ошибка: {e}"))
            logger.exception("Критическая ошибка в create_solana_wallets")

        self.stdout.write(f"\n=== Создание завершено ===")