"""Celery tasks for the *crypto* domain.

На первом этапе задачи-"заглушки" фиксируют структуру и обеспечивают
корректную регистрацию в Celery. Реальная работа с блокчейном будет
добавлена по мере готовности интеграционных драйверов.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from celery import shared_task
from django.utils import timezone
from django.db import transaction

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from transactions.models import Transaction, Transfer  # noqa: E402  pylint: disable=wrong-import-position
from .models import SystemWalletAddress, UserDepositMemo, UserWallet
from .blockchain.tron import get_trc20_transfers, extract_deposit_events

logger = logging.getLogger(__name__)


@shared_task
def check_blockchain_deposits() -> str:
    """Periodic task that scans blockchains for new incoming deposits.

    Пока что просто пишет в лог и возвращает количество обработанных
    транзакций. Реальная логика будет реализована после подключения
    конкретных драйверов (Tron, EVM, BTC и т.д.).
    """
    logger.info("[check_blockchain_deposits] started at %s", timezone.now())

    processed = 0

    channel_layer = get_channel_layer()

    # Обрабатываем TRC20-кошельки
    wallets = SystemWalletAddress.objects.filter(network__iexact="TRC20", currency__is_active=True)
    for wallet in wallets:
        # Определяем с какого времени искать (последний зафиксированный депозит)
        last_tx = Transaction.objects.filter(crypto=wallet.currency, tx_hash__isnull=False).order_by("-timestamp").first()
        min_ts = 0
        if last_tx:
            min_ts = int(last_tx.timestamp.timestamp() * 1000)  # ms
        logger.info(f"[check_blockchain_deposits] Fetching transfers for address {wallet.address} with min_timestamp: {min_ts}")
        try:
            raw = get_trc20_transfers(wallet.address, min_ts)
            events = extract_deposit_events(raw)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("[check_blockchain_deposits] error fetch %s: %s", wallet.address, exc)
            continue

        for ev in events:
            memo = ev.get("memo")
            if not memo:
                continue  # требуется Memo для связи с пользователем
            try:
                deposit_memo = UserDepositMemo.objects.select_related("user", "currency").get(memo=memo, currency=wallet.currency, status="waiting")
            except UserDepositMemo.DoesNotExist:
                continue  # чужое memo или уже подтверждено
            # Проверяем дубликаты
            if Transaction.objects.filter(tx_hash=ev["tx_hash"]).exists():
                continue

            # Создаём запись о переводе и обновляем баланс пользователя
            with transaction.atomic():
                Transaction.objects.create(
                    user=deposit_memo.user,
                    crypto=wallet.currency,
                    amount=Decimal(ev["amount"]),
                    type="deposit",
                    status="completed",
                    tx_hash=ev["tx_hash"],
                    timestamp=ev["timestamp"],
                )
                # Обновляем баланс пользователя
                user_wallet, _ = UserWallet.objects.get_or_create(user=deposit_memo.user, currency=wallet.currency)
                user_wallet.balance = user_wallet.balance + Decimal(ev["amount"])
                user_wallet.save(update_fields=["balance"])

                deposit_memo.status = "used"
                deposit_memo.save(update_fields=["status"])
                processed += 1

                # Отправляем сообщение через WebSocket
                async_to_sync(channel_layer.group_send)(
                    f'deposit_memo_{deposit_memo.memo}',
                    {
                        'type': 'deposit_status',
                        'status': deposit_memo.status
                    }
                )

    logger.info("[check_blockchain_deposits] finished, processed=%s", processed)
    return str(processed)


@shared_task(bind=True)
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
