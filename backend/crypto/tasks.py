"""Celery tasks for the *crypto* domain.

На первом этапе задачи-"заглушки" фиксируют структуру и обеспечивают
корректную регистрацию в Celery. Реальная работа с блокчейном будет
добавлена по мере готовности интеграционных драйверов.
"""
from __future__ import annotations

import os
import logging
import traceback
from decimal import Decimal
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)
from django.utils import timezone
from django.db import transaction

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from transactions.models import Transaction, Transfer  # noqa: E402  pylint: disable=wrong-import-position
from .models import SystemWalletAddress, UserDepositMemo, UserWallet
from .blockchain.tron import get_trc20_transfers, extract_deposit_events
from tronpy import Tron

logger = logging.getLogger(__name__)


@shared_task
def check_blockchain_deposits():
    """
    Периодическая задача для проверки новых депозитов в блокчейне.
    """
    processed = 0
    logger.info("[check_blockchain_deposits] Starting deposit check...")

    wallets = SystemWalletAddress.objects.filter(network__iexact="TRC20", currency__is_active=True)
    logger.info(f"[check_blockchain_deposits] Found {wallets.count()} TRC20 wallets to check")

    for wallet in wallets:
        try:
            logger.info(f"[check_blockchain_deposits] Checking wallet: {wallet.address} for currency {wallet.currency.symbol}")
            
            last_tx = Transaction.objects.filter(crypto=wallet.currency, tx_hash__isnull=False).order_by("-timestamp").first()
            min_ts = int(last_tx.timestamp.timestamp() * 1000) if last_tx else 0
            logger.info(f"Checking from timestamp: {min_ts}")

            events = get_trc20_transfers(address=wallet.address, min_timestamp=min_ts)
            logger.info(f"Found {len(events)} events for wallet {wallet.address}")

            if not events:
                continue

            for ev in events:
                memo = ev.get("memo")
                tx_hash = ev.get("transaction_id")
                amount_str = ev.get("value")

                logger.info(f"Processing Event: tx_hash={tx_hash}, memo='{memo}', amount='{amount_str}'")

                if not memo:
                    logger.warning("Skipping event due to empty memo.")
                    continue

                try:
                    # Используем filter() и first() на случай дубликатов, но ожидаем один
                    deposit_memo = UserDepositMemo.objects.filter(memo=memo, status="waiting").first()
                    if not deposit_memo:
                        logger.warning(f"No waiting UserDepositMemo found for memo='{memo}'.")
                        continue
                    logger.info(f"Found UserDepositMemo: id={deposit_memo.id} for memo='{memo}'")

                except Exception as e:
                    logger.error(f"Error while fetching memo '{memo}': {e}", exc_info=True)
                    continue
                
                if Transaction.objects.filter(tx_hash=tx_hash).exists():
                    logger.warning(f"Duplicate transaction found: tx_hash={tx_hash}. Skipping.")
                    continue

                try:
                    amount = Decimal(amount_str) / Decimal(10**wallet.currency.decimals)
                except (ValueError, TypeError):
                    logger.error(f"Invalid amount format: {amount_str}. Skipping.")
                    continue

                try:
                    with transaction.atomic():
                        logger.info(f"Updating balance for user {deposit_memo.user.id} and wallet {wallet.currency.symbol}")
                        user_wallet, _ = UserWallet.objects.get_or_create(user=deposit_memo.user, currency=wallet.currency)
                        user_wallet.balance += amount
                        user_wallet.save()

                        Transaction.objects.create(
                            user=deposit_memo.user,
                            crypto=wallet.currency,
                            amount=amount,
                            tx_hash=tx_hash,
                            type="deposit",
                            status="completed",
                            timestamp=timezone.now()
                        )

                        deposit_memo.status = "used"
                        deposit_memo.save()
                        
                        processed += 1
                        logger.info(f"Successfully processed deposit for memo='{memo}', tx_hash={tx_hash}")

                except Exception as e:
                    logger.error(f"Error during database transaction for memo='{memo}': {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error processing wallet {wallet.address}: {e}", exc_info=True)

    logger.info(f"Finished deposit check. Processed {processed} transactions.")
    return f"Готово, обработано: {processed}"


@shared_task(bind=True, name='crypto.tasks.process_withdrawal')
def process_withdrawal(self, transfer_id: int) -> str:  # pylint: disable=unused-argument
    """Processes a *pending* withdrawal transfer.

    Args:
        transfer_id: PK of the ``Transfer`` instance representing withdrawal.

    Returns:
        tx_hash (str): Blockchain transaction hash (placeholder for now).
    """
    try:
        transfer: Transfer = Transfer.objects.select_for_update().get(id=transfer_id)
    except Transfer.DoesNotExist:  # pragma: no cover
        logger.error("[process_withdrawal] transfer %s not found", transfer_id)
        return "error:not_found"

    if transfer.status != Transfer.Status.PENDING:  # type: ignore[attr-defined]
        logger.info("[process_withdrawal] transfer %s not pending, skip", transfer_id)
        return "skip:not_pending"

    # Placeholder: mark as SUCCESS instantly and pretend fee calculation
    tx_hash = f"stub-{transfer_id}-{timezone.now().timestamp()}"
    fee = Decimal("0.0001")  # TODO: dynamic fee based on currency/network

    with transaction.atomic():
        transfer.tx_hash = tx_hash  # type: ignore[attr-defined]
        transfer.fee = fee  # type: ignore[attr-defined]
        transfer.status = Transfer.Status.SUCCESS  # type: ignore[attr-defined]
        transfer.completed_at = timezone.now()  # type: ignore[attr-defined]
        transfer.save(update_fields=["tx_hash", "fee", "status", "completed_at"])

    logger.info("[process_withdrawal] transfer %s completed -> %s", transfer.id, tx_hash)
    return tx_hash
