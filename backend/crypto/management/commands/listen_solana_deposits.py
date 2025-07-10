"""Django management command для отслеживания депозитов USDT в сети Solana (SPL)."""
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
from crypto.blockchain.solana import get_spl_usdt_transfers, extract_deposit_events, SolanaError

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Отслеживает депозиты USDT в сети Solana (SPL)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--once',
            action='store_true',
            help='Выполнить однократную проверку и завершить',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Запуск отслеживания депозитов Solana (SPL)...'))

        if not os.getenv('SOLANA_RPC_URL'):
            self.stdout.write(self.style.ERROR('❌ SOLANA_RPC_URL не установлен в переменных окружения'))
            sys.exit(1)

        blockchain_state, created = BlockchainState.objects.get_or_create(
            blockchain='solana',
            defaults={'last_processed_block': 0}
        )
        if created:
            self.stdout.write(self.style.WARNING('⚠️  Создано новое состояние блокчейна Solana'))

        try:
            if options['once']:
                self._process_deposits_once(blockchain_state)
            else:
                self._run_continuous_monitoring(blockchain_state)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\n⏹️  Отслеживание остановлено пользователем'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Критическая ошибка: {e}'))
            logger.exception("Критическая ошибка в listen_solana_deposits")
            sys.exit(1)

    def _process_deposits_once(self, blockchain_state):
        self.stdout.write('🔍 Выполняется однократная проверка депозитов...')
        wallets = SystemWalletAddress.objects.filter(
            network__iexact="SPL",
            currency__is_active=True
        )
        if not wallets.exists():
            self.stdout.write(self.style.WARNING('⚠️  Не найдено активных кошельков SPL'))
            return
        processed_count = 0
        for wallet in wallets:
            try:
                last_tx = Transaction.objects.filter(
                    crypto=wallet.currency,
                    tx_hash__isnull=False
                ).order_by('-timestamp').first()
                min_slot = int(blockchain_state.last_processed_block) if blockchain_state.last_processed_block else 0
                transfers = get_spl_usdt_transfers(wallet.address, min_slot)
                events = extract_deposit_events(transfers)
                if events:
                    processed = self._process_events(events, wallet)
                    processed_count += processed
                    self.stdout.write(f'✅ Обработано {processed} депозитов для {wallet.currency.symbol}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Ошибка обработки кошелька {wallet.address}: {e}'))
        self.stdout.write(self.style.SUCCESS(f'🎉 Однократная проверка завершена. Обработано: {processed_count}'))

    def _run_continuous_monitoring(self, blockchain_state):
        self.stdout.write('🔄 Запуск непрерывного отслеживания...')
        self.stdout.write('   Нажмите Ctrl+C для остановки')
        while True:
            try:
                wallets = SystemWalletAddress.objects.filter(
                    network__iexact="SPL",
                    currency__is_active=True
                )
                if not wallets.exists():
                    self.stdout.write(self.style.WARNING('⚠️  Не найдено активных кошельков SPL'))
                    time.sleep(30)
                    continue
                for wallet in wallets:
                    try:
                        last_tx = Transaction.objects.filter(
                            crypto=wallet.currency,
                            tx_hash__isnull=False
                        ).order_by('-timestamp').first()
                        min_slot = int(blockchain_state.last_processed_block) if blockchain_state.last_processed_block else 0
                        transfers = get_spl_usdt_transfers(wallet.address, min_slot)
                        events = extract_deposit_events(transfers)
                        if events:
                            processed = self._process_events(events, wallet)
                            if processed > 0:
                                self.stdout.write(f'✅ Обработано {processed} новых депозитов для {wallet.currency.symbol}')
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'❌ Ошибка обработки кошелька {wallet.address}: {e}'))
                        logger.exception(f"Ошибка обработки кошелька {wallet.address}")
                blockchain_state.updated_at = django_timezone.now()
                blockchain_state.save()
                time.sleep(30)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Ошибка в основном цикле: {e}'))
                logger.exception("Ошибка в основном цикле мониторинга")
                time.sleep(60)

    def _process_events(self, events, wallet):
        processed_count = 0
        for event in events:
            try:
                tx_hash = event.get('tx_hash')
                memo = event.get('memo')
                amount = event.get('amount')
                if Transaction.objects.filter(tx_hash=tx_hash).exists():
                    logger.info(f"Транзакция {tx_hash} уже обработана, пропускаем")
                    continue
                deposit_memo = UserDepositMemo.objects.filter(
                    memo=memo,
                    status="waiting",
                    currency=wallet.currency,
                    network="SPL"
                ).first()
                if not deposit_memo:
                    logger.warning(f"Не найден ожидающий мемо-код для: {memo}")
                    continue
                if deposit_memo.expires_at < django_timezone.now():
                    logger.warning(f"Мемо-код {memo} истек")
                    deposit_memo.status = "expired"
                    deposit_memo.save()
                    continue
                with transaction.atomic():
                    user_wallet, _ = UserWallet.objects.get_or_create(
                        user=deposit_memo.user,
                        currency=wallet.currency
                    )
                    user_wallet.balance += Decimal(str(amount))
                    user_wallet.save()
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
                    Transaction.objects.create(
                        user=deposit_memo.user,
                        crypto=wallet.currency,
                        amount=Decimal(str(amount)),
                        tx_hash=tx_hash,
                        type="deposit",
                        status="completed",
                        timestamp=django_timezone.now()
                    )
                    deposit_memo.status = "used"
                    deposit_memo.save()
                    processed_count += 1
                    logger.info(f"Успешно обработан депозит: {tx_hash}, мемо: {memo}")
            except Exception as e:
                logger.error(f"Ошибка обработки события {event}: {e}", exc_info=True)
        return processed_count 