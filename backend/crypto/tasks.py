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
from .models import Cryptocurrency

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

    # 1. Сначала обрабатываем валюты с MEMO (как раньше)
    for wallet in SystemWalletAddress.objects.select_related('currency').all():
        currency = wallet.currency
        if not currency.is_active:
            continue
        if not getattr(currency, 'requires_memo', False):
            logger.info(f"Skipping {currency.symbol} in {wallet.network}: MEMO not required (per official docs)")
            continue

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

    # 2. Теперь обрабатываем валюты без MEMO/tag по уникальным адресам пользователей
    currencies_no_memo = Cryptocurrency.objects.filter(is_active=True, requires_memo=False)
    for currency in currencies_no_memo:
        user_wallets = UserWallet.objects.filter(currency=currency, is_system_wallet=False, deposit_address__isnull=False).exclude(deposit_address='')
        for user_wallet in user_wallets:
            address = user_wallet.deposit_address
            logger.info(f"[no-memo][DEBUG] SCAN: currency={currency.symbol}, network={currency.network}, user={user_wallet.user_id}, address={address}")
            try:
                service = get_blockchain_service(currency.network or currency.symbol)
            except ValueError:
                logger.warning(f"Unsupported network {currency.network} for {currency.symbol}. Skipping.")
                continue
            # Получаем последние транзакции по адресу
            last_tx = Transaction.objects.filter(crypto=currency, tx_hash__isnull=False, user=user_wallet.user).order_by("-timestamp").first()
            min_ts = int(last_tx.timestamp.timestamp() * 1000) if last_tx else 0
            logger.info(f"[no-memo][DEBUG] CALL get_transactions: address={address}, min_ts={min_ts}, contract={currency.contract_address}")
            raw_transactions = service.get_transactions(address=address, min_timestamp=min_ts)
            logger.info(f"[no-memo] Found {len(raw_transactions)} tx for {currency.symbol} address {address}")
            for ev in raw_transactions:
                tx_hash = ev.get("transaction_id")
                amount_str = ev.get("value")
                logger.info(f"[no-memo] Processing: {currency.symbol} {address} tx={tx_hash} amount={amount_str}")
                if Transaction.objects.filter(tx_hash=tx_hash).exists():
                    logger.info(f"[no-memo] Duplicate tx {tx_hash}, skipping.")
                    continue
                try:
                    amount = Decimal(amount_str) / Decimal(10**currency.decimals)
                except (ValueError, TypeError):
                    logger.error(f"[no-memo] Invalid amount: {amount_str}")
                    continue
                with transaction.atomic():
                    user_wallet.balance += amount
                    user_wallet.save()
                    Transaction.objects.create(
                        user=user_wallet.user,
                        crypto=currency,
                        amount=amount,
                        tx_hash=tx_hash,
                        type="deposit",
                        status="completed",
                        timestamp=timezone.now()
                    )
                    logger.info(f"[no-memo] Deposit credited: {user_wallet.user} {currency.symbol} {amount}")

                # Отправляем WebSocket сигнал по адресу
                try:
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f"deposit_address_{address}",
                        {
                            "type": "deposit_status_update",
                            "data": {
                                "address": address,
                                "currency": currency.symbol,
                                "network": currency.network,
                                "status": "used",
                                "amount": str(amount),
                            }
                        }
                    )
                    logger.info(f"[no-memo] WebSocket signal sent for address {address}")
                except Exception as e:
                    logger.error(f"[no-memo] Failed to send WebSocket signal for address {address}: {e}")

    # --- XRP Ledger ---
    xrp_wallets = SystemWalletAddress.objects.filter(network__iexact="XRP", currency__is_active=True)
    logger.info(f"[check_blockchain_deposits] Found {xrp_wallets.count()} XRP wallets to check")
    for wallet in xrp_wallets:
        try:
            logger.info(f"[check_blockchain_deposits][XRP] Checking wallet: {wallet.address} for currency {wallet.currency.symbol}")
            # Получаем последние обработанные транзакции (можно доработать для оптимизации)
            last_tx = Transaction.objects.filter(crypto=wallet.currency, tx_hash__isnull=False).order_by("-timestamp").first()
            # XRP Ledger не использует timestamp, а ledger index. Для простоты пока не фильтруем по ledger.
            incoming_txs = get_xrp_incoming_transactions(wallet.address)
            logger.info(f"[check_blockchain_deposits][XRP] Found {len(incoming_txs)} incoming payments for {wallet.address}")
            for tx in incoming_txs:
                tx_hash = tx.get("hash")
                amount_drops = int(tx.get("Amount", 0))
                amount = Decimal(amount_drops) / Decimal(1_000_000)  # 1 XRP = 1_000_000 drops
                destination_tag = str(tx.get("DestinationTag", ""))
                logger.info(f"[check_blockchain_deposits][XRP] Processing tx_hash={tx_hash}, tag={destination_tag}, amount={amount}")
                if not destination_tag:
                    logger.warning("[XRP] Skipping tx without DestinationTag (memo)")
                    continue
                if Transaction.objects.filter(tx_hash=tx_hash).exists():
                    logger.warning(f"[XRP] Duplicate transaction found: tx_hash={tx_hash}. Skipping.")
                    continue
                deposit_memo = UserDepositMemo.objects.filter(memo=destination_tag, status="waiting").first()
                if not deposit_memo:
                    logger.warning(f"[XRP] No waiting UserDepositMemo found for tag='{destination_tag}'.")
                    continue
                with transaction.atomic():
                    user_wallet, _ = UserWallet.objects.get_or_create(user=deposit_memo.user, currency=wallet.currency)
                    user_wallet.balance += amount
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
                    system_wallet.balance += amount
                    system_wallet.save()
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
                    logger.info(f"[XRP] Successfully processed deposit for tag='{destination_tag}', tx_hash={tx_hash}")
        except Exception as e:
            logger.error(f"[XRP] Error processing wallet {wallet.address}: {e}", exc_info=True)

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
    from transactions.models import Withdrawal
    
    pending_withdrawals = Withdrawal.objects.filter(
        transaction__status='pending',
        is_email_confirmed=True
    )
    
    for withdrawal in pending_withdrawals:
        # Здесь можно добавить дополнительную логику, если требуется,
        # например, создание объекта Transfer перед вызовом задачи.
        # На данный момент, предполагаем, что `process_withdrawal` 
        # может быть вызван с ID вывода.
        
        # Найдем или создадим соответствующий Transfer
        from transactions.models import Transfer
        transfer, created = Transfer.objects.get_or_create(
            user=withdrawal.user,
            amount=withdrawal.transaction.amount,
            status=Transfer.Status.PENDING,
            # Можно добавить связь с withdrawal, если ее нет
        )
        
        if created:
            logger.info(f"Created new Transfer {transfer.id} for Withdrawal {withdrawal.id}")
        
        logger.info(f"Processing pending withdrawal {withdrawal.id} via transfer {transfer.id}")
        process_withdrawal.delay(transfer.id)

@shared_task
def process_pending_deposits():
    """
    Периодическая задача для обработки всех ожидающих депозитов (если требуется).
    """
    # Здесь можно реализовать обработку зависших депозитов, если такая логика нужна
    pass
