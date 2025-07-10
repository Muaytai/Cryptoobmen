"""Django management command для отслеживания депозитов Ethereum (ERC20).

Команда работает аналогично listen_deposits.py, но для Ethereum блокчейна.
Отслеживает депозиты USDT в сети ERC20 и обновляет балансы пользователей.
"""
import os
import sys
import time
import logging
from datetime import datetime, timezone
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone as django_timezone
from django.conf import settings

from crypto.models import (
    Cryptocurrency, SystemWalletAddress, UserDepositMemo, 
    UserWallet, BlockchainState
)
from transactions.models import Transaction
from crypto.blockchain.ethereum import get_erc20_transfers, extract_deposit_events, EthereumError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Отслеживает депозиты USDT в сети Ethereum (ERC20)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--smart-start',
            action='store_true',
            help='Умный старт: обработает пропущенные блоки за последние 24 часа',
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Выполнить однократную проверку и завершить',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Запуск отслеживания депозитов Ethereum (ERC20)...')
        )

        # Проверяем настройки
        if not os.getenv('ETHERSCAN_API_KEY'):
            self.stdout.write(
                self.style.ERROR('❌ ETHERSCAN_API_KEY не установлен в переменных окружения')
            )
            sys.exit(1)

        if not os.getenv('ETHEREUM_RPC_URL'):
            self.stdout.write(
                self.style.ERROR('❌ ETHEREUM_RPC_URL не установлен в переменных окружения')
            )
            sys.exit(1)

        # Получаем или создаем состояние блокчейна
        blockchain_state, created = BlockchainState.objects.get_or_create(
            blockchain='ethereum',
            defaults={'last_processed_block': 0}
        )

        if created:
            self.stdout.write(
                self.style.WARNING('⚠️  Создано новое состояние блокчейна Ethereum')
            )

        # Умный старт: обрабатываем пропущенные блоки
        if options['smart_start']:
            self.stdout.write('🔄 Выполняется умный старт...')
            self._smart_start(blockchain_state)

        # Основной цикл отслеживания
        try:
            if options['once']:
                self._process_deposits_once(blockchain_state)
            else:
                self._run_continuous_monitoring(blockchain_state)
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\n⏹️  Отслеживание остановлено пользователем')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Критическая ошибка: {e}')
            )
            logger.exception("Критическая ошибка в listen_ethereum_deposits")
            sys.exit(1)

    def _smart_start(self, blockchain_state):
        """Обрабатывает пропущенные блоки за последние 24 часа."""
        try:
            # Получаем все системные кошельки ERC20
            wallets = SystemWalletAddress.objects.filter(
                network__iexact="ERC20",
                currency__is_active=True
            )

            if not wallets.exists():
                self.stdout.write(
                    self.style.WARNING('⚠️  Не найдено активных кошельков ERC20')
                )
                return

            self.stdout.write(f'🔍 Найдено {wallets.count()} кошельков ERC20')

            # Обрабатываем каждый кошелек
            for wallet in wallets:
                self.stdout.write(f'📊 Обработка кошелька: {wallet.address}')
                
                try:
                    # Получаем последнюю транзакцию для этого кошелька
                    last_tx = Transaction.objects.filter(
                        crypto=wallet.currency,
                        tx_hash__isnull=False
                    ).order_by('-timestamp').first()

                    if last_tx:
                        min_timestamp = int(last_tx.timestamp.timestamp() * 1000)
                        self.stdout.write(f'   📅 Проверка с: {datetime.fromtimestamp(min_timestamp/1000)}')
                    else:
                        # Если нет транзакций, проверяем за последние 24 часа
                        min_timestamp = int((django_timezone.now() - django_timezone.timedelta(hours=24)).timestamp() * 1000)
                        self.stdout.write(f'   📅 Проверка за последние 24 часа')

                    # Получаем транзакции
                    transfers = get_erc20_transfers(wallet.address, min_timestamp)
                    events = extract_deposit_events(transfers)

                    if events:
                        self.stdout.write(f'   ✅ Найдено {len(events)} новых депозитов')
                        self._process_events(events, wallet)
                    else:
                        self.stdout.write(f'   ℹ️  Новых депозитов не найдено')

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'   ❌ Ошибка обработки кошелька {wallet.address}: {e}')
                    )
                    logger.exception(f"Ошибка в smart_start для кошелька {wallet.address}")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка умного старта: {e}')
            )
            logger.exception("Ошибка в smart_start")

    def _process_deposits_once(self, blockchain_state):
        """Выполняет однократную проверку депозитов."""
        self.stdout.write('🔍 Выполняется однократная проверка депозитов...')
        
        wallets = SystemWalletAddress.objects.filter(
            network__iexact="ERC20",
            currency__is_active=True
        )

        if not wallets.exists():
            self.stdout.write(
                self.style.WARNING('⚠️  Не найдено активных кошельков ERC20')
            )
            return

        processed_count = 0
        for wallet in wallets:
            try:
                # Получаем последнюю транзакцию
                last_tx = Transaction.objects.filter(
                    crypto=wallet.currency,
                    tx_hash__isnull=False
                ).order_by('-timestamp').first()

                min_timestamp = int(last_tx.timestamp.timestamp() * 1000) if last_tx else 0

                # Получаем новые транзакции
                transfers = get_erc20_transfers(wallet.address, min_timestamp)
                events = extract_deposit_events(transfers)

                if events:
                    processed = self._process_events(events, wallet)
                    processed_count += processed
                    self.stdout.write(f'✅ Обработано {processed} депозитов для {wallet.currency.symbol}')

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Ошибка обработки кошелька {wallet.address}: {e}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'🎉 Однократная проверка завершена. Обработано: {processed_count}')
        )

    def _run_continuous_monitoring(self, blockchain_state):
        """Запускает непрерывное отслеживание депозитов."""
        self.stdout.write('🔄 Запуск непрерывного отслеживания...')
        self.stdout.write('   Нажмите Ctrl+C для остановки')

        while True:
            try:
                # Получаем активные кошельки ERC20
                wallets = SystemWalletAddress.objects.filter(
                    network__iexact="ERC20",
                    currency__is_active=True
                )

                if not wallets.exists():
                    self.stdout.write(
                        self.style.WARNING('⚠️  Не найдено активных кошельков ERC20')
                    )
                    time.sleep(30)
                    continue

                # Обрабатываем каждый кошелек
                for wallet in wallets:
                    try:
                        # Получаем последнюю транзакцию
                        last_tx = Transaction.objects.filter(
                            crypto=wallet.currency,
                            tx_hash__isnull=False
                        ).order_by('-timestamp').first()

                        min_timestamp = int(last_tx.timestamp.timestamp() * 1000) if last_tx else 0

                        # Получаем новые транзакции
                        transfers = get_erc20_transfers(wallet.address, min_timestamp)
                        events = extract_deposit_events(transfers)

                        if events:
                            processed = self._process_events(events, wallet)
                            if processed > 0:
                                self.stdout.write(
                                    f'✅ Обработано {processed} новых депозитов для {wallet.currency.symbol}'
                                )

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'❌ Ошибка обработки кошелька {wallet.address}: {e}')
                        )
                        logger.exception(f"Ошибка обработки кошелька {wallet.address}")

                # Обновляем состояние блокчейна
                blockchain_state.updated_at = django_timezone.now()
                blockchain_state.save()

                # Ждем перед следующей проверкой
                time.sleep(30)  # Проверяем каждые 30 секунд

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Ошибка в основном цикле: {e}')
                )
                logger.exception("Ошибка в основном цикле мониторинга")
                time.sleep(60)  # Ждем дольше при ошибке

    def _process_events(self, events, wallet):
        """Обрабатывает события депозитов."""
        processed_count = 0

        for event in events:
            try:
                tx_hash = event.get('tx_hash')
                memo = event.get('memo')
                amount = event.get('amount')

                # Проверяем, не обработана ли уже эта транзакция
                if Transaction.objects.filter(tx_hash=tx_hash).exists():
                    logger.info(f"Транзакция {tx_hash} уже обработана, пропускаем")
                    continue

                # Ищем соответствующий мемо-код
                deposit_memo = UserDepositMemo.objects.filter(
                    memo=memo,
                    status="waiting",
                    currency=wallet.currency,
                    network="ERC20"
                ).first()

                if not deposit_memo:
                    logger.warning(f"Не найден ожидающий мемо-код для: {memo}")
                    continue

                # Проверяем, не истек ли мемо-код
                if deposit_memo.expires_at < django_timezone.now():
                    logger.warning(f"Мемо-код {memo} истек")
                    deposit_memo.status = "expired"
                    deposit_memo.save()
                    continue

                # Обрабатываем депозит
                with transaction.atomic():
                    # Обновляем баланс пользователя
                    user_wallet, _ = UserWallet.objects.get_or_create(
                        user=deposit_memo.user,
                        currency=wallet.currency
                    )
                    user_wallet.balance += Decimal(str(amount))
                    user_wallet.save()

                    # Обновляем системный кошелек
                    system_wallet, _ = UserWallet.objects.get_or_create(
                        user=None,
                        currency=wallet.currency,
                        defaults={
                            'balance': Decimal('0'),
                            'is_system_wallet': True,
                            'is_active': True,
                        }
                    )
                    system_wallet.balance += Decimal(str(amount))
                    system_wallet.save()

                    # Создаем запись о транзакции
                    Transaction.objects.create(
                        user=deposit_memo.user,
                        crypto=wallet.currency,
                        amount=Decimal(str(amount)),
                        tx_hash=tx_hash,
                        type="deposit",
                        status="completed",
                        timestamp=django_timezone.now()
                    )

                    # Отмечаем мемо-код как использованный
                    deposit_memo.status = "used"
                    deposit_memo.save()

                    processed_count += 1
                    logger.info(f"Успешно обработан депозит: {tx_hash}, мемо: {memo}")

            except Exception as e:
                logger.error(f"Ошибка обработки события {event}: {e}", exc_info=True)

        return processed_count 