from __future__ import annotations

import os
import logging
import traceback
from decimal import Decimal
from celery import shared_task
from celery.utils.log import get_task_logger

from django.utils import timezone
from django.db import transaction

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import SystemWalletAddress, UserDepositMemo, UserWallet, CommissionTransaction
from .blockchain.factory import get_blockchain_service
from django.conf import settings

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


@shared_task
def check_blockchain_deposits():
    """
    Периодическая задача для проверки новых депозитов в блокчейне.
    """
    from transactions.models import Transaction
    from .models import SystemWalletAddress, UserDepositMemo, UserWallet
    processed = 0
    logger.info("[check_blockchain_deposits] Starting deposit check...")

    # Получаем все активные системные кошельки, а не только TRC20
    wallets = SystemWalletAddress.objects.filter(currency__is_active=True)
    logger.info(f"[check_blockchain_deposits] Found {wallets.count()} wallets to check across all networks")

    for wallet in wallets:
        try:
            logger.info(f"[check_blockchain_deposits] Checking wallet: {wallet.address} for currency {wallet.currency.symbol} in network {wallet.network}")
            
            last_tx = Transaction.objects.filter(crypto=wallet.currency, tx_hash__isnull=False).order_by("-timestamp").first()
            min_ts = int(last_tx.timestamp.timestamp() * 1000) if last_tx else 0
            logger.info(f"Checking from timestamp: {min_ts}")

            # Используем фабрику для получения нужного сервиса
            try:
                service = get_blockchain_service(wallet.network)
            except ValueError:
                logger.warning(f"Unsupported network {wallet.network} for wallet {wallet.address}. Skipping.")
                continue
            
            raw_transactions = service.get_transactions(address=wallet.address, min_timestamp=min_ts)
            
            logger.info(f"Found {len(raw_transactions)} raw transactions for wallet {wallet.address}")

            if not raw_transactions:
                continue

            for ev in raw_transactions:
                memo = ev.get("memo")
                tx_hash = ev.get("transaction_id")
                amount_str = ev.get("value")

                logger.info(f"Processing Event: tx_hash={tx_hash}, memo='{memo}', amount='{amount_str}'")

                user = None
                deposit_memo = None

                # Логика определения пользователя по транзакции
                if memo:
                    # Если есть memo, всегда пытаемся найти пользователя по нему
                    try:
                        deposit_memo = UserDepositMemo.objects.filter(memo=memo, status="waiting").first()
                        if deposit_memo:
                            user = deposit_memo.user
                        else:
                            logger.warning(f"No waiting UserDepositMemo found for memo='{memo}'. Skipping.")
                            continue
                    except Exception as e:
                        logger.error(f"Error while fetching memo '{memo}': {e}", exc_info=True)
                        continue
                
                elif wallet.currency.requires_memo:
                    # Если memo обязательно, но его нет, пропускаем
                    logger.warning(f"Skipping event for {wallet.currency.symbol} because it requires a memo, but none was provided.")
                    continue
                
                else:
                    # Если memo не обязателен и его нет (например, BTC)
                    # TODO: Реализовать логику для валют без memo (поиск по уникальному адресу)
                    logger.info(f"Skipping deposit for {wallet.currency.symbol} as it does not require memo and no memo was provided (logic not implemented).")
                    continue
                
                if not user:
                    logger.warning(f"User not found for transaction {tx_hash}. Skipping.")
                    continue

                # Проверяем на дубликат ДО основной логики
                if Transaction.objects.filter(tx_hash=tx_hash).exists():
                    logger.warning(f"Duplicate transaction found: tx_hash={tx_hash}. Re-sending signal just in case.")
                    # Отправляем сигнал повторно, на случай если фронтенд его пропустил
                    if deposit_memo:
                        channel_layer = get_channel_layer()
                        async_to_sync(channel_layer.group_send)(
                            f"deposit_memo_{deposit_memo.memo}",
                            {
                                "type": "deposit_status_update",
                                "data": {'memo': deposit_memo.memo, 'status': 'used', 'message': 'Deposit completed'}
                            }
                        )
                    continue

                try:
                    amount = Decimal(amount_str) / Decimal(10**wallet.currency.decimals)
                except (ValueError, TypeError):
                    logger.error(f"Invalid amount format: {amount_str}. Skipping.")
                    continue

                try:
                    with transaction.atomic():
                        logger.info(f"Updating balance for user {user.id} and wallet {wallet.currency.symbol}")
                        user_wallet, _ = UserWallet.objects.get_or_create(user=user, currency=wallet.currency)
                        user_wallet.balance += amount
                        user_wallet.save()

                        system_wallet, _ = UserWallet.objects.get_or_create(
                            user=None,
                            currency=wallet.currency,
                            defaults={'balance': Decimal('0'), 'is_system_wallet': True, 'is_active': True}
                        )
                        system_wallet.balance += amount
                        system_wallet.save()

                        Transaction.objects.create(
                            user=user,
                            crypto=wallet.currency,
                            amount=amount,
                            tx_hash=tx_hash,
                            type="deposit",
                            status="completed",
                            timestamp=timezone.now()
                        )

                        if deposit_memo:
                            deposit_memo.status = "used"
                            deposit_memo.save()
                        
                        processed += 1
                        logger.info(f"Successfully processed deposit for user {user.id}, tx_hash={tx_hash}")

                    # После успешной транзакции отправляем сигнал
                    if deposit_memo:
                        logger.info(f"!!! SENDING WEBSOCKET SIGNAL for memo {deposit_memo.memo} !!!")
                        channel_layer = get_channel_layer()
                        async_to_sync(channel_layer.group_send)(
                            f"deposit_memo_{deposit_memo.memo}",
                            {
                                "type": "deposit_status_update",
                                "data": {
                                    'memo': deposit_memo.memo,
                                    'status': 'used',
                                    'message': 'Deposit completed'
                                }
                            }
                        )
                        logger.info(f"!!! WEBSOCKET SIGNAL SENT for memo {deposit_memo.memo} !!!")

                except Exception as e:
                    logger.error(f"Error during database transaction for memo='{memo}': {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error processing wallet {wallet.address}: {e}", exc_info=True)

    logger.info(f"Finished deposit check. Processed {processed} transactions.")
    return f"Готово, обработано: {processed}"


@shared_task(bind=True, name='crypto.tasks.process_withdrawal')
def process_withdrawal(self, transfer_id: int) -> str:
    from transactions.models import Transfer, Withdrawal

    tx_hash = None  # Инициализируем tx_hash
    try:
        with transaction.atomic():
            try:
                transfer = Transfer.objects.select_for_update().get(id=transfer_id)
            except Transfer.DoesNotExist:
                logger.error("[process_withdrawal] transfer %s not found", transfer_id)
                return "error:not_found"

            if transfer.status != Transfer.Status.PENDING:
                logger.info("[process_withdrawal] transfer %s not pending, skip", transfer_id)
                return "skip:not_pending"

            withdrawal = Withdrawal.objects.filter(
                user=transfer.user,
                transaction__amount=transfer.amount,
                transaction__status='pending'
            ).order_by('-id').first()

            if not withdrawal:
                logger.error(f"[process_withdrawal] No matching Withdrawal for transfer {transfer_id}")
                raise Exception("No matching Withdrawal found")

            try:
                network = withdrawal.transaction.crypto.network
                currency = withdrawal.transaction.crypto

                system_wallet = UserWallet.objects.filter(
                    currency=currency,
                    is_system_wallet=True,
                    is_active=True
                ).first()

                if not system_wallet or not system_wallet.encrypted_private_key:
                    raise Exception(f"Активный системный кошелек для {currency.symbol} ({network}) не найден или не имеет приватного ключа.")

                priv_key = system_wallet.encrypted_private_key
                to_address = withdrawal.destination_address
                amount = transfer.amount
                memo = f"withdrawal_{withdrawal.id}_{transfer.id}"

                service = get_blockchain_service(network)
                tx_hash = service.send_transaction(priv_key, to_address, amount, memo)
                
                fee = Decimal("0.0001")  # TODO: вычислять реальную комиссию
                status = Transfer.Status.SUCCESS
                withdrawal.transaction.status = 'completed'
                withdrawal.transaction.tx_hash = tx_hash
                withdrawal.transaction.save(update_fields=["status", "tx_hash"])
                withdrawal.confirmation_date = timezone.now()
                withdrawal.save(update_fields=["confirmation_date"])

            except Exception as e:
                logger.error(f"[process_withdrawal] Ошибка отправки: {e}", exc_info=True)
                tx_hash = None
                fee = None
                status = Transfer.Status.FAILED
                withdrawal.transaction.status = 'failed'
                withdrawal.transaction.save(update_fields=["status"])
                raise

            transfer.tx_hash = tx_hash
            transfer.fee = fee
            transfer.status = status
            transfer.completed_at = timezone.now()
            transfer.save(update_fields=["tx_hash", "fee", "status", "completed_at"])

    except Exception as e:
        logger.error(f"Critical error in process_withdrawal for transfer {transfer_id}: {e}", exc_info=True)
        return "error:transaction_failed"

    logger.info("[process_withdrawal] transfer %s completed -> %s", transfer.id, tx_hash)
    return tx_hash or "error:tx_failed"


@shared_task
def process_pending_withdrawals():
    """
    Периодическая задача для обработки всех ожидающих заявок на вывод.
    """
    from transactions.models import Transfer
    pending_transfers = Transfer.objects.filter(status=Transfer.Status.PENDING)
    for transfer in pending_transfers:
        process_withdrawal.delay(transfer.id)

@shared_task
def process_pending_deposits():
    """
    Периодическая задача для обработки всех ожидающих депозитов (если требуется).
    """
    # Здесь можно реализовать обработку зависших депозитов, если такая логика нужна
    pass
