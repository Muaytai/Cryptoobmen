from __future__ import annotations
import os
import logging
import traceback
from decimal import Decimal
from celery import shared_task
from celery.utils.log import get_task_logger
from celery.exceptions import Retry
from crypto.blockchain.xrp import XRPService
from django.utils import timezone
from django.db import transaction
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import time
from typing import List, Dict, Any, Tuple
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import SystemWalletAddress, UserDepositMemo, UserWallet, CommissionTransaction
from .blockchain.factory import get_blockchain_service
from django.conf import settings
from .models import Cryptocurrency
from .gas_calculation import calculate_net_deposit_amount, calculate_withdrawal_gas_cost
logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)
from core.task_lock import single_instance_task
from .tasks_consolidation import get_gas_reserve, get_min_consolidation_amount
from django.utils import timezone
from .batch_rpc import cached_batch_processor

# Кэш для балансов и транзакций (время жизни 30 секунд)
@lru_cache(maxsize=1000)
def get_cached_balance(service_class: str, address: str, timestamp: int) -> str:
    """Кэширование балансов с временной меткой"""
    try:
        service = get_blockchain_service(service_class)
        balance = service.get_balance(address)
        return str(balance)
    except Exception as e:
        logger.error(f"Error getting cached balance for {address}: {e}")
        return "0"

def get_balance_with_cache(service, address: str, cache_seconds: int = 30) -> Decimal:
    """Получение баланса с кэшированием"""
    current_time = int(time.time())
    cache_key = current_time // cache_seconds
    service_class = service.__class__.__name__
    balance_str = get_cached_balance(service_class, address, cache_key)
    return Decimal(balance_str)

def process_single_address(args: Tuple) -> Tuple[str, List[Dict[str, Any]], bool]:
    """Обрабатывает один адрес в параллельном потоке"""
    (currency, user_wallet, last_tx_timestamp) = args
    address = user_wallet.deposit_address
    user_id = user_wallet.user.id
    try:
        logger.info(f"[PARALLEL] Processing {currency.symbol} for user {user_id}, address {address}")
        service = get_blockchain_service(currency.network or currency.symbol)
        balance = cached_batch_processor.get_cached_balance(service, address)
        if balance == 0:
            logger.debug(f"[PARALLEL] Zero balance for {address}, skipping")
            return (address, [], False)
        if currency.symbol == 'POL':
            current_block = service.w3.eth.block_number
            from_block = max(current_block - 500, 1)
            logger.info(f"[PARALLEL][POL] Optimized scan: blocks {from_block} to {current_block} for {address}")
            if hasattr(service, 'optimized_scanner') and service.optimized_scanner:
                raw_transactions = service.optimized_scanner.scan_optimized([address], from_block, current_block)
            else:
                raw_transactions = service.get_transactions(address=address, from_block=from_block, to_block=current_block)
        elif currency.network and currency.network.upper() == 'ERC20':
            raw_transactions = service.get_transactions(
                address=address,
                min_timestamp=last_tx_timestamp,
                contract_address=currency.contract_address
            )
        else:
            raw_transactions = service.get_transactions(address=address, min_timestamp=last_tx_timestamp)
        logger.info(f"[PARALLEL] Found {len(raw_transactions)} transactions for {address}")
        return (address, raw_transactions, True)
    except Exception as e:
        logger.error(f"[PARALLEL] Error processing {address}: {e}")
        return (address, [], False)

def process_addresses_batch(currency, user_wallets, service) -> Dict[str, Tuple[List[Dict[str, Any]], bool]]:
    """
    Обрабатывает множество адресов одной валюты батчами
    """
    logger.info(f"[BATCH] Starting batch processing for {len(user_wallets)} addresses of {currency.symbol}")
    addresses = [wallet.deposit_address for wallet in user_wallets]
    address_to_wallet = {wallet.deposit_address: wallet for wallet in user_wallets}

    is_solana = (currency.symbol.upper() == 'SOL') or ((currency.network or '').lower() == 'solana')

    if not is_solana:
        contract_address = (
            currency.contract_address
            if currency.network and currency.network.upper() == 'TRC20'
            else None
        )
        balances = cached_batch_processor.batch_get_balances_cached(service, addresses, contract_address)
    else:
        balances = {addr: Decimal('1') for addr in addresses}

    active_addresses = []
    transaction_params = []

    if not is_solana:
        for address, balance in balances.items():
            if balance <= 0:
                continue
            wallet = address_to_wallet[address]
            from transactions.models import Transaction
            last_tx = Transaction.objects.filter(
                user=wallet.user,
                crypto=currency,
                tx_hash__isnull=False
            ).order_by("-timestamp").first()
            min_ts = int(last_tx.timestamp.timestamp() * 1000) if last_tx else 0
            active_addresses.append(address)
            if currency.symbol == 'POL':
                current_block = service.w3.eth.block_number
                from_block = max(current_block - 500, 1)
                params = {'from_block': from_block, 'to_block': current_block}
            elif currency.network and currency.network.upper() in ('ERC20', 'TRC20'):
                params = {'min_timestamp': min_ts, 'contract_address': currency.contract_address}
            else:
                params = {'min_timestamp': min_ts}
            transaction_params.append((address, params))
    else:
        from transactions.models import Transaction
        from datetime import timedelta
        for address in addresses:
            wallet = address_to_wallet[address]
            last_tx = Transaction.objects.filter(
                user=wallet.user,
                crypto=currency,
                tx_hash__isnull=False
            ).order_by("-timestamp").first()
            if last_tx:
                widened_time = last_tx.timestamp - timedelta(hours=24)
                min_ts = int(widened_time.timestamp() * 1000)
            else:
                min_ts = 0
            active_addresses.append(address)
            params = {'min_timestamp': min_ts}
            transaction_params.append((address, params))

    if is_solana:
        logger.info(f"[BATCH] (SOL) Processing all {len(active_addresses)} addresses with timestamp filtering")
    else:
        logger.info(f"[BATCH] Found {len(active_addresses)} addresses with balance > 0 for {currency.symbol}")

    results = {}
    if transaction_params:
        if currency.symbol == 'POL' and hasattr(service, 'optimized_scanner') and service.optimized_scanner:
            logger.info(f"[BATCH][POL] Using optimized scanner for {len(active_addresses)} addresses")
            current_block = service.w3.eth.block_number
            from_block = max(current_block - 500, 1)
            try:
                all_transactions = service.optimized_scanner.scan_optimized(active_addresses, from_block, current_block)
                transactions_by_address = {}
                for tx in all_transactions:
                    to_addr = tx.get('to_address', '').lower()
                    if to_addr in [addr.lower() for addr in active_addresses]:
                        if to_addr not in transactions_by_address:
                            transactions_by_address[to_addr] = []
                        transactions_by_address[to_addr].append(tx)
                for address in active_addresses:
                    addr_lower = address.lower()
                    txs = transactions_by_address.get(addr_lower, [])
                    results[address] = (txs, True)
            except Exception as e:
                logger.error(f"[BATCH][POL] Optimized scanner failed: {e}, falling back to batch RPC")
                all_transactions = cached_batch_processor.batch_get_transactions(service, transaction_params)
                for address, txs in all_transactions.items():
                    results[address] = (txs, True)
        else:
            all_transactions = cached_batch_processor.batch_get_transactions(service, transaction_params)
            for address, txs in all_transactions.items():
                results[address] = (txs, True)

    for address in addresses:
        if address not in results:
            results[address] = ([], False)

    logger.info(f"[BATCH] Completed batch processing for {currency.symbol}: {len(results)} addresses processed")
    return results

@shared_task
@single_instance_task(timeout=300)
def check_blockchain_deposits():
    from transactions.models import Transaction
    from .models import SystemWalletAddress, UserDepositMemo, UserWallet
    processed = 0
    logger.info("[check_blockchain_deposits] Starting deposit check...")

    # 1. Валюты с MEMO
    for wallet in SystemWalletAddress.objects.select_related('currency').all():
        currency = wallet.currency
        if not currency.is_active or not getattr(currency, 'requires_memo', False):
            continue
        logger.info(f"[check_blockchain_deposits] Checking wallet: {wallet.address} for {currency.symbol}")
        last_tx = Transaction.objects.filter(crypto=currency, tx_hash__isnull=False).order_by("-timestamp").first()
        min_ts = int(last_tx.timestamp.timestamp() * 1000) if last_tx else 0
        try:
            service = get_blockchain_service(wallet.network)
        except ValueError:
            logger.warning(f"Unsupported network {wallet.network}. Skipping.")
            continue
        raw_transactions = service.get_transactions(address=wallet.address, min_timestamp=min_ts)
        for ev in raw_transactions:
            memo = ev.get("memo")
            tx_hash = ev.get("transaction_id")
            amount_str = ev.get("value")
            user = None
            deposit_memo = None
            if memo:
                deposit_memo = UserDepositMemo.objects.filter(memo=memo, status="waiting").first()
                if deposit_memo:
                    user = deposit_memo.user
                else:
                    logger.warning(f"No waiting memo for '{memo}'. Skipping.")
                    continue
            elif currency.requires_memo:
                logger.warning(f"Skipping {currency.symbol}: memo required but missing.")
                continue
            if not user:
                logger.warning(f"User not found for {tx_hash}. Skipping.")
                continue

            if Transaction.objects.filter(tx_hash=tx_hash).exists():
                logger.warning(f"Duplicate tx {tx_hash}. Re-sending signal.")
                if deposit_memo:
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f"deposit_memo_{deposit_memo.memo}",
                        {"type": "deposit_status_update", "data": {'memo': deposit_memo.memo, 'status': 'used'}}
                    )
                continue

            try:
                amount = Decimal(amount_str) / Decimal(10**currency.decimals)
            except (ValueError, TypeError):
                logger.error(f"Invalid amount: {amount_str}. Skipping.")
                continue

            try:
                with transaction.atomic():
                    user_wallet, _ = UserWallet.objects.get_or_create(user=user, currency=currency)
                    user_wallet.balance += amount
                    user_wallet.save()

                    system_wallet, _ = UserWallet.objects.get_or_create(
                        user=None, currency=currency,
                        defaults={'balance': Decimal('0'), 'is_system_wallet': True, 'is_active': True}
                    )
                    system_wallet.balance += amount
                    system_wallet.save()

                    Transaction.objects.create(
                        user=user,
                        crypto=currency,
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
                    
                    # Немедленная попытка консолидации для pending депозитов
                    # Используем countdown=3 чтобы дать время транзакции БД коммититься (предотвращаем race condition)
                    if deposit_status == "pending":
                        logger.info(f"🚀 [IMMEDIATE] Triggering immediate consolidation for pending deposit {tx_hash} (with 3s delay to avoid race condition)")
                        from .tasks_consolidation import consolidate_user_deposits
                        consolidate_user_deposits.apply_async(countdown=3)

                # После успешной транзакции отправляем сигнал
                if deposit_memo:
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f"deposit_memo_{deposit_memo.memo}",
                        {"type": "deposit_status_update", "data": {'memo': deposit_memo.memo, 'status': 'used'}}
                    )
            except Exception as e:
                logger.error(f"DB error for memo='{memo}': {e}")

    # 2. Валюты без MEMO
    currencies_no_memo = Cryptocurrency.objects.filter(is_active=True, requires_memo=False)
    for currency in currencies_no_memo:
        logger.info(f"[BATCH] Processing {currency.symbol} (network={currency.network})")
        user_wallets = UserWallet.objects.filter(
            currency=currency,
            is_system_wallet=False,
            deposit_address__isnull=False
        ).exclude(deposit_address='')
        if not user_wallets.exists():
            continue
        try:
            service = get_blockchain_service(currency.network or currency.symbol)
            batch_results = process_addresses_batch(currency, user_wallets, service)
            address_to_wallet = {w.deposit_address: w for w in user_wallets}
            for address, (raw_txs, success) in batch_results.items():
                if not success or not raw_txs:
                    continue
                user_wallet = address_to_wallet.get(address)
                if not user_wallet:
                    continue
                for ev in raw_txs:
                    tx_hash = ev.get("transaction_id")
                    amount_str = ev.get("value")
                    existing_tx = Transaction.objects.filter(tx_hash=tx_hash, user=user_wallet.user).first()
                    if existing_tx:
                        if existing_tx.status == 'completed':
                            continue
                        elif existing_tx.status == 'pending':
                            processed += 1
                            continue
                        else:
                            continue

                    try:
                        if '.' in amount_str and Decimal(amount_str) < Decimal('1000') and currency.symbol == 'POL':
                            amount = Decimal(amount_str)
                        elif currency.network and currency.network.upper() == 'ERC20':
                            if currency.symbol == 'ETH':
                                amount = Decimal(amount_str) / Decimal(10**18)
                            else:
                                amount = Decimal(amount_str) / Decimal(10**currency.decimals)
                        else:
                            amount = Decimal(amount_str) / Decimal(10**currency.decimals)
                    except (ValueError, TypeError) as e:
                        logger.error(f"[BATCH] Invalid amount: {amount_str}, error: {e}")
                        continue

                    deposit_status = "pending"
                    net_amount = amount
                    gas_cost = Decimal('0')
                    if not currency.requires_memo:
                        deposit_info = calculate_net_deposit_amount(currency=currency, deposit_amount=amount, user_address=address)
                        gas_cost = deposit_info['gas_cost']

                    with transaction.atomic():
                        Transaction.objects.create(
                            user=user_wallet.user,
                            crypto=currency,
                            amount=net_amount,
                            fee=gas_cost,
                            tx_hash=tx_hash,
                            type="deposit",
                            status=deposit_status,
                            timestamp=timezone.now()
                        )
                        processed += 1
                        logger.info(f"[BATCH] Deposit recorded with status '{deposit_status}': {user_wallet.user} {currency.symbol} {amount} (balance NOT credited for no-MEMO currencies)")
                        
                        # Немедленная попытка консолидации для pending депозитов
                        # ⚠️ ВАЖНО: Консолидация работает с балансом блокчейна, а НЕ с балансом в БД!
                        # Используем countdown=3 чтобы дать время транзакции БД коммититься (предотвращаем race condition)
                        if deposit_status == "pending":
                            logger.info(f"🚀 [IMMEDIATE] Triggering immediate consolidation for pending deposit {tx_hash} (with 3s delay to avoid race condition)")
                            from .tasks_consolidation import consolidate_user_deposits
                            consolidate_user_deposits.apply_async(countdown=3)

                    try:
                        channel_layer = get_channel_layer()
                        async_to_sync(channel_layer.group_send)(
                            f"deposit_address_{address}",
                            {"type": "deposit_status_update", "data": {
                                "address": address,
                                "currency": currency.symbol,
                                "network": currency.network,
                                "status": "used",
                                "amount": str(amount),
                            }}
                        )
                    except Exception as e:
                        logger.error(f"[BATCH] WS error for {address}: {e}")

        except Exception as e:
            logger.error(f"[BATCH] Error processing {currency.symbol}: {e}")
            continue
        try:
            cached_batch_processor.cleanup_cache()
        except Exception as cache_error:
            logger.warning(f"[BATCH] Cache cleanup failed: {cache_error}")

    # XRP Ledger
    xrp_wallets = SystemWalletAddress.objects.filter(network__iexact="XRP", currency__is_active=True)
    for wallet in xrp_wallets:
        try:
            service = XRPService()
            incoming_txs = service.get_transactions(wallet.address)
            for ev in incoming_txs:
                memo = ev.get("memo")
                tx_hash = ev.get("transaction_id")
                amount_str = ev.get("value")
                if not memo or not wallet.currency.requires_memo:
                    continue
                deposit_memo = UserDepositMemo.objects.filter(memo=memo, status="waiting").first()
                if not deposit_memo:
                    continue
                user = deposit_memo.user
                if Transaction.objects.filter(tx_hash=tx_hash).exists():
                    continue
                decimals = getattr(wallet.currency, 'decimals', 6) or 6
                amount = Decimal(amount_str) / Decimal(10**decimals)
                with transaction.atomic():
                    user_wallet, _ = UserWallet.objects.get_or_create(user=user, currency=wallet.currency)
                    user_wallet.balance += amount
                    user_wallet.save()
                    system_wallet, _ = UserWallet.objects.get_or_create(
                        user=None, currency=wallet.currency,
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
                    deposit_memo.status = "used"
                    deposit_memo.save()
                    processed += 1
                    logger.info(f"[XRP] Successfully processed deposit for tag='{memo}', tx_hash={tx_hash}")
        except Exception as e:
            logger.error(f"[XRP] Error: {e}", exc_info=True)

    logger.info(f"Finished deposit check. Processed {processed} transactions.")
    if processed > 0:
        process_pending_deposits.delay()
    return f"Готово, обработано: {processed}"

@shared_task(bind=True, name='crypto.tasks.process_withdrawal')
def process_withdrawal(self, withdrawal_id: int) -> str:
    logger.info(f"--- Starting processing for withdrawal_id: {withdrawal_id} ---")
    from transactions.models import Withdrawal
    from .models import CommissionWallet, CommissionTransaction
    try:
        withdrawal = Withdrawal.objects.select_related(
            'transaction', 'wallet', 'user', 'transaction__crypto'
        ).get(id=withdrawal_id)
    except Withdrawal.DoesNotExist:
        logger.error(f"Withdrawal with id {withdrawal_id} not found.")
        return f"error:not_found"
    try:
        crypto = withdrawal.transaction.crypto
        amount_to_send = withdrawal.transaction.amount
        platform_fee = withdrawal.transaction.fee
        gas_cost = calculate_withdrawal_gas_cost(
            currency=crypto,
            withdrawal_amount=amount_to_send,
            destination_address=withdrawal.destination_address
        )
        total_amount = amount_to_send + platform_fee + gas_cost
        with transaction.atomic():
            withdrawal = Withdrawal.objects.select_for_update().get(id=withdrawal_id)
            if not withdrawal.is_email_confirmed:
                return f"skip:not_confirmed"
            if withdrawal.transaction.status in ['awaiting_confirmation', 'completed', 'failed']:
                if withdrawal.transaction.tx_hash:
                    logger.warning(f"Withdrawal {withdrawal_id} already processed.")
                    return f"skip:already_processed:{withdrawal.transaction.status}"
            user_wallet = UserWallet.objects.select_for_update().get(id=withdrawal.wallet.id)
            if user_wallet.balance < total_amount:
                withdrawal.transaction.status = 'failed'
                withdrawal.transaction.notes = f"Insufficient funds. Required: {total_amount}"
                withdrawal.transaction.save()
                logger.error(f"Insufficient funds for withdrawal {withdrawal.id}.")
                return "error:insufficient_funds"
            user_wallet.balance -= total_amount
            user_wallet.locked_balance += total_amount
            user_wallet.save()
            withdrawal.transaction.status = 'processing'
            withdrawal.transaction.save()
            from transactions.models import Transfer
            transfer, created = Transfer.objects.get_or_create(
                withdrawal=withdrawal,
                defaults={
                    'user': withdrawal.user,
                    'amount': withdrawal.transaction.amount,
                    'status': Transfer.Status.PENDING,
                    'type': 'out'
                }
            )
        network = crypto.network or crypto.symbol
        system_wallet = UserWallet.objects.get(currency=crypto, is_system_wallet=True, is_active=True)
        if not system_wallet.encrypted_private_key:
            raise Exception(f"System wallet for {crypto.symbol} has no private key.")
        service = get_blockchain_service(network)
        tx_kwargs = {
            'private_key': system_wallet.encrypted_private_key,
            'to_address': withdrawal.destination_address,
            'amount': amount_to_send,
            'memo': f"withdrawal_{withdrawal.id}"
        }
        if network.upper() in ('ERC20', 'TRC20'):
            tx_kwargs['contract_address'] = crypto.contract_address
        tx_hash = service.send_transaction(**tx_kwargs)
        with transaction.atomic():
            withdrawal.transaction.tx_hash = tx_hash
            withdrawal.transaction.status = 'awaiting_confirmation'
            withdrawal.transaction.save()
            commission_wallet, _ = CommissionWallet.objects.get_or_create(currency=crypto)
            commission_wallet.balance += platform_fee
            commission_wallet.save()
            CommissionTransaction.objects.create(
                user=withdrawal.user,
                currency=crypto,
                amount=platform_fee,
                commission_type='withdraw',
                related_object_id=str(withdrawal.transaction.transaction_id)
            )
        check_withdrawal_confirmation.apply_async(args=[withdrawal.id], countdown=60)
        logger.info(f"Withdrawal {withdrawal.id} sent with tx_hash: {tx_hash}")
        return f"success:sent_to_network:{tx_hash}"
    except Exception as e:
        logger.error(f"!!! Exception for withdrawal {withdrawal_id} !!!", exc_info=True)
        if withdrawal:
            with transaction.atomic():
                withdrawal_to_fail = Withdrawal.objects.select_for_update().get(id=withdrawal_id)
                user_wallet_to_refund = UserWallet.objects.select_for_update().get(id=withdrawal_to_fail.wallet.id)
                amount_to_refund = withdrawal_to_fail.transaction.amount + withdrawal_to_fail.transaction.fee
                if user_wallet_to_refund.locked_balance >= amount_to_refund:
                    user_wallet_to_refund.locked_balance -= amount_to_refund
                    user_wallet_to_refund.balance += amount_to_refund
                    user_wallet_to_refund.save()
                withdrawal_to_fail.transaction.status = 'failed'
                withdrawal_to_fail.transaction.notes = f"Transaction error: {str(e)}. Funds refunded."
                withdrawal_to_fail.transaction.save()
        return f"error:transaction_failed - {str(e)}"

@shared_task
def process_pending_withdrawals():
    from transactions.models import Withdrawal
    from django.db.models import Q
    stuck_withdrawals = Withdrawal.objects.filter(
        Q(transaction__status='pending') | Q(transaction__status='processing'),
        is_email_confirmed=True,
        transaction__tx_hash__isnull=True
    )
    logger.info(f"Found {stuck_withdrawals.count()} stuck withdrawals")
    for withdrawal in stuck_withdrawals:
        logger.info(f"Re-queueing processing for withdrawal {withdrawal.id}")
        process_withdrawal.delay(withdrawal.id)
    awaiting_confirmation_withdrawals = Withdrawal.objects.filter(
        transaction__status='awaiting_confirmation',
        is_email_confirmed=True
    )
    logger.info(f"Found {awaiting_confirmation_withdrawals.count()} awaiting confirmation withdrawals")
    for withdrawal in awaiting_confirmation_withdrawals:
        logger.info(f"Queueing blockchain confirmation check for withdrawal {withdrawal.id}")
        check_withdrawal_confirmation.delay(withdrawal.id)

def process_consolidation_for_wallet(args: Tuple) -> Tuple[bool, str, Decimal, Decimal]:
    (currency, user_wallet, blockchain_service, system_wallet_address, min_threshold) = args
    try:
        contract_address = currency.contract_address if currency.network and currency.network.upper() in ('TRC20', 'ERC20') else None
        blockchain_balance = cached_batch_processor.get_cached_balance(blockchain_service, user_wallet.deposit_address, contract_address)
        if blockchain_balance < min_threshold:
            return (False, user_wallet.deposit_address, Decimal('0'), Decimal('0'))
        if hasattr(blockchain_service, 'get_max_sendable_amount'):
            amount_to_send = blockchain_service.get_max_sendable_amount(user_wallet.deposit_address, system_wallet_address)
            if amount_to_send <= 0:
                return (False, user_wallet.deposit_address, Decimal('0'), Decimal('0'))
            gas_cost = blockchain_balance - amount_to_send
        else:
            gas_reserve = get_gas_reserve(currency)
            amount_to_send = blockchain_balance - gas_reserve
            gas_cost = gas_reserve
            if amount_to_send <= 0:
                return (False, user_wallet.deposit_address, Decimal('0'), Decimal('0'))
        private_key_input = user_wallet.encrypted_private_key or ""
        if not private_key_input:
            from crypto.models import GeneratedWallet
            gw = GeneratedWallet.objects.filter(address=user_wallet.deposit_address).first()
            if gw and gw.private_key:
                private_key_input = gw.private_key
            else:
                return (False, user_wallet.deposit_address, Decimal('0'), Decimal('0'))
        tx_hash = blockchain_service.send_transaction(
            private_key=private_key_input,
            to_address=system_wallet_address,
            amount=amount_to_send,
            contract_address=contract_address,
        )
        return (True, tx_hash, amount_to_send, gas_cost)
    except Exception as e:
        logger.error(f"[CONSOLIDATION] Error: {e}")
        return (False, user_wallet.deposit_address, Decimal('0'), Decimal('0'))

@shared_task
def process_pending_deposits():
    from transactions.models import Transaction
    from crypto.models import Cryptocurrency, UserWallet
    from .tasks_consolidation import get_min_consolidation_amount, get_system_wallet_address
    from .blockchain.factory import get_blockchain_service
    from django.utils import timezone
    from datetime import timedelta
    logger.info("🔄 Processing pending deposits for consolidation...")
    currencies = Cryptocurrency.objects.filter(requires_memo=False, is_active=True)
    consolidated_count = 0
    for currency in currencies:
        try:
            service = get_blockchain_service(currency.network or currency.symbol)
            system_addr = get_system_wallet_address(currency)
            user_wallets = UserWallet.objects.filter(
                currency=currency, is_system_wallet=False, deposit_address__isnull=False
            ).exclude(deposit_address='')
            if not user_wallets.exists():
                continue
            min_threshold = get_min_consolidation_amount(currency)
            recent_window = timezone.now() - timedelta(hours=24)
            args_list = []
            for w in user_wallets:
                has_recent = Transaction.objects.filter(
                    user=w.user, crypto=currency, type="deposit", status="pending", timestamp__gte=recent_window
                ).exists()
                if has_recent:
                    args_list.append((currency, w, service, system_addr, min_threshold))
            max_workers = min(5, len(args_list))
            with ThreadPoolExecutor(max_workers=max_workers) as exe:
                futures = {exe.submit(process_consolidation_for_wallet, a): a[1] for a in args_list}
                for future in as_completed(futures):
                    wallet = futures[future]
                    try:
                        success, tx_hash, amount_sent, gas_cost = future.result(timeout=120)
                        if success and not Transaction.objects.filter(tx_hash=tx_hash).exists():
                            with transaction.atomic():
                                Transaction.objects.create(
                                    user=wallet.user,
                                    crypto=currency,
                                    amount=amount_sent,
                                    type="consolidation",
                                    status="pending",
                                    tx_hash=tx_hash,
                                    timestamp=timezone.now(),
                                    fee=gas_cost
                                )
                                consolidated_count += 1
                    except Exception as e:
                        logger.error(f"[CONSOLIDATION] Error: {e}")
        except Exception as e:
            logger.error(f"Error processing {currency.symbol}: {e}")
    logger.info(f"🏁 Consolidation completed: {consolidated_count} transactions")
    return f"Consolidation completed: {consolidated_count} transactions"

@shared_task(bind=True, max_retries=20, default_retry_delay=60)
def check_withdrawal_confirmation(self, withdrawal_id: int):
    from transactions.models import Withdrawal
    withdrawal = None
    try:
        withdrawal = Withdrawal.objects.select_related('transaction', 'wallet', 'user').get(id=withdrawal_id)
        if withdrawal.transaction.status != 'awaiting_confirmation':
            return f"skip:not_awaiting_confirmation"
        tx_hash = withdrawal.transaction.tx_hash
        if not tx_hash:
            withdrawal.transaction.status = 'failed'
            withdrawal.transaction.notes = "Missing tx_hash."
            withdrawal.transaction.save()
            return "error:missing_tx_hash"
        service = get_blockchain_service(withdrawal.transaction.crypto.network)
        is_confirmed = service.is_transaction_confirmed(tx_hash)
        if is_confirmed:
            gas_cost = calculate_withdrawal_gas_cost(
                currency=withdrawal.transaction.crypto,
                withdrawal_amount=withdrawal.transaction.amount,
                destination_address=withdrawal.destination_address
            )
            amount_to_withdraw = withdrawal.transaction.amount + withdrawal.transaction.fee + gas_cost
            with transaction.atomic():
                user_wallet = UserWallet.objects.select_for_update().get(id=withdrawal.wallet.id)
                
                # Повторная проверка заблокированного баланса на всякий случай
                # При подтверждении проверяем locked_balance, так как средства уже были зарезервированы при отправке
                # ⚠️ ВАЖНО: Используем небольшую дельту для учета погрешностей округления Decimal
                # (разница в 0.000000000001 не должна блокировать подтверждение)
                delta = Decimal('0.000001')  # Допустимая погрешность для сравнения
                
                if user_wallet.locked_balance < (amount_to_withdraw - delta):
                    withdrawal.transaction.status = 'failed'
                    withdrawal.transaction.notes = f"Insufficient locked funds discovered upon withdrawal confirmation. Required: {amount_to_withdraw} (including gas: {gas_cost})"
                    withdrawal.transaction.save()
                    logger.error(f"Insufficient locked funds for withdrawal {withdrawal.id} upon confirmation. Locked balance: {user_wallet.locked_balance}, required: {amount_to_withdraw}")
                    return "error:insufficient_locked_funds_on_confirmation"

                # Списываем средства (включая газ)
                # Средства уже были списаны с основного баланса,
                # теперь нужно уменьшить заблокированный баланс
                # ⚠️ ВАЖНО: Используем max() чтобы избежать отрицательного баланса из-за погрешностей округления
                user_wallet.locked_balance = max(Decimal('0'), user_wallet.locked_balance - amount_to_withdraw)
                user_wallet.save()
                
                logger.info(f"Withdrawal {withdrawal_id} completed: {amount_to_withdraw} deducted (amount: {withdrawal.transaction.amount}, platform_fee: {withdrawal.transaction.fee}, gas: {gas_cost})")

                # Обновляем транзакцию
                # ⚠️ КРИТИЧЕСКИ ВАЖНО: Сохраняем транзакцию в той же атомарной транзакции,
                # чтобы сигнал не сработал преждевременно и не вернул средства
                withdrawal.transaction.status = 'completed'
                withdrawal.transaction.save()
                
                # Обновляем сам вывод
                withdrawal.confirmation_date = timezone.now()
                withdrawal.save()

            logger.info(f"Successfully finalized withdrawal {withdrawal.id}.")
            return f"success:confirmed_and_completed"
        else:
            if self.request.retries >= self.max_retries:
                withdrawal.transaction.status = 'failed'
                withdrawal.transaction.save()
                return f"error:max_retries_exceeded"
            retry_countdown = 60 * (self.request.retries + 1)
            raise self.retry(countdown=retry_countdown, max_retries=self.max_retries)
    except Withdrawal.DoesNotExist:
        return f"error:not_found"
    except Retry:
        raise
    except Exception as e:
        if self.request.retries >= self.max_retries:
            if withdrawal:
                withdrawal.transaction.status = 'failed'
                withdrawal.transaction.save()
            return f"error:max_retries_exceeded"
        retry_countdown = 60 * (self.request.retries + 1)
        raise self.retry(countdown=retry_countdown, exc=e, max_retries=self.max_retries)

@shared_task
def consolidate_funds():
    logger.info("[CONSOLIDATE] Starting funds consolidation task.")
    currencies_to_consolidate = Cryptocurrency.objects.filter(is_active=True, requires_memo=False)
    for currency in currencies_to_consolidate:
        logger.info(f"[CONSOLIDATE] Processing currency: {currency.symbol}")
        try:
            service = get_blockchain_service(currency.network or currency.symbol)
            system_wallet_address = SystemWalletAddress.objects.get(currency=currency).address
            contract_address = currency.contract_address if currency.network and currency.network.upper() in ('TRC20', 'ERC20') else None
            if contract_address:
                test_balance = service.get_balance(system_wallet_address, contract_address=contract_address)
            else:
                test_balance = service.get_balance(system_wallet_address)
            user_wallets = UserWallet.objects.filter(
                currency=currency,
                is_system_wallet=False,
                deposit_address__isnull=False
            ).exclude(deposit_address='')
            for u_wallet in user_wallets:
                try:
                    if hasattr(service, '__class__') and 'Tron' in service.__class__.__name__ and contract_address:
                        actual_balance = service.get_balance(u_wallet.deposit_address, contract_address=contract_address)
                    else:
                        actual_balance = service.get_balance(u_wallet.deposit_address)
                except TypeError:
                    # Fallback для сервисов, которые не поддерживают contract_address
                    actual_balance = service.get_balance(u_wallet.deposit_address)
                
                # Используем настроенный минимальный порог
                min_threshold = get_min_consolidation_amount(currency) 
                
                if actual_balance < min_threshold:
                    logger.info(f"[CONSOLIDATE] Skipping user {u_wallet.user.id} wallet for {currency.symbol}: balance {actual_balance} is below threshold {min_threshold}.")
                    continue

                logger.info(f"[CONSOLIDATE] Consolidating {actual_balance} {currency.symbol} from user {u_wallet.user.id} address {u_wallet.deposit_address}")

                # Используем приватный ключ текущего депозитного адреса пользователя
                private_key = getattr(u_wallet, "encrypted_private_key", None)
                if not private_key:
                    logger.warning(f"[CONSOLIDATE] Skip user {u_wallet.user.id} for {currency.symbol}: missing private key for address {u_wallet.deposit_address}")
                    continue

                # Рассчитываем максимальную отправляемую сумму (баланс - газ)
                if hasattr(service, 'get_max_sendable_amount'):
                    # Для POL используем умный расчёт газа
                    max_sendable = service.get_max_sendable_amount(u_wallet.deposit_address, system_wallet_address)
                    if max_sendable <= 0:
                        logger.warning(f"[CONSOLIDATE] Cannot consolidate for user {u_wallet.user.id}: insufficient balance after gas deduction")
                        continue
                    amount_to_send = max_sendable
                    logger.info(f"[CONSOLIDATE] Smart gas calculation: sending {amount_to_send} {currency.symbol} (from balance {actual_balance})")
                else:
                    # Fallback для других валют - вычитаем фиксированный резерв
                    gas_reserve = get_gas_reserve(currency)
                    amount_to_send = actual_balance - gas_reserve
                    if amount_to_send <= 0:
                        logger.warning(f"[CONSOLIDATE] Cannot consolidate for user {u_wallet.user.id}: insufficient balance after gas reserve")
                        continue
                    logger.info(f"[CONSOLIDATE] Fixed gas reserve: sending {amount_to_send} {currency.symbol} (gas reserve: {gas_reserve})")

                # Для TRC-20 токенов проверяем наличие TRX для оплаты газа
                if currency.network and currency.network.upper() == 'TRC20':
                    # Получаем баланс TRX на адресе
                    trx_balance = service.get_balance(u_wallet.deposit_address)  # Без contract_address для TRX
                    
                    # Если TRX недостаточно для оплаты газа, отправляем TRX с системного кошелька
                    min_trx_for_gas = Decimal('3')  # Минимум TRX для оплаты газа
                    if trx_balance < min_trx_for_gas:
                        logger.info(f"[CONSOLIDATE] Insufficient TRX ({trx_balance}) for gas on address {u_wallet.deposit_address}. Need to send TRX first.")
                        
                        # Получаем системный TRX кошелек
                        try:
                            trx_currency = Cryptocurrency.objects.get(symbol='TRX', network='TRC20')
                            system_trx_wallet = SystemWalletAddress.objects.get(currency=trx_currency)
                            
                            # Отправляем TRX для оплаты газа
                            trx_service = get_blockchain_service('TRC20')
                            trx_amount = min_trx_for_gas - trx_balance
                            
                            logger.info(f"[CONSOLIDATE] Sending {trx_amount} TRX to {u_wallet.deposit_address} for gas payment")
                            
                            # Используем приватный ключ системного TRX кошелька
                            system_trx_private_key = SystemWalletAddress.objects.get(currency=trx_currency).private_key
                            
                            gas_tx_hash = trx_service.send_transaction(
                                private_key=system_trx_private_key,
                                to_address=u_wallet.deposit_address,
                                amount=trx_amount,
                            )
                            
                            logger.info(f"[CONSOLIDATE] TRX gas payment sent: {gas_tx_hash}")
                            
                            # Ждем подтверждения TRX транзакции
                            import time
                            time.sleep(10)  # Ждем 10 секунд для подтверждения
                            
                        except Exception as gas_error:
                            logger.error(f"[CONSOLIDATE] Failed to send TRX for gas payment: {gas_error}")
                            continue

                # Отправляем средства на системный кошелек
                # Передаём contract_address для токенов (иначе отправится нативная монета)
                tx_hash = service.send_transaction(
                    private_key=private_key,
                    to_address=system_wallet_address,
                    amount=amount_to_send,
                    contract_address=contract_address,
                )
                
                logger.info(f"[CONSOLIDATE] Consolidation transaction sent for user {u_wallet.user.id}. Tx hash: {tx_hash}")

                # Сохраняем транзакцию консолидации в БД
                try:
                    from transactions.models import Transaction
                    if not Transaction.objects.filter(tx_hash=tx_hash).exists():
                        Transaction.objects.create(
                            user=u_wallet.user,
                            crypto=currency,
                            amount=amount_to_send,
                            type="consolidation",
                            status="pending",
                            tx_hash=tx_hash,
                            timestamp=timezone.now(),
                            fee=gas_cost
                        )
                except Exception as e:
                    logger.error(f"[CONSOLIDATE] Error for user {u_wallet.user.id}: {e}")
        except Exception as e:
            logger.warning(f"[CONSOLIDATE] Service error for {currency.symbol}: {e}")
    logger.info("[CONSOLIDATE] Finished funds consolidation task.")

@shared_task
def sync_balances_with_blockchain():
    """
    Синхронизирует балансы в базе данных с реальными балансами в блокчейне.
    
    ⚠️ ВАЖНО:
    - Для системных кошельков: синхронизирует баланс с балансом в блокчейне
    - Для пользовательских кошельков: синхронизирует ТОЛЬКО для валют С MEMO
    - Для валют БЕЗ MEMO: НЕ синхронизирует, так как баланс пользователя в БД = зачисленные средства после консолидации,
      а баланс на депозитном адресе = средства, которые еще не консолидированы
    """
    logger.info("[BALANCE_SYNC] Starting balance synchronization with blockchain...")
    
    from .models import UserWallet, Cryptocurrency
    
    synced_count = 0
    error_count = 0
    system_wallets = UserWallet.objects.filter(is_system_wallet=True, currency__is_active=True)
    for wallet in system_wallets:
        try:
            if not wallet.deposit_address:
                continue
            service = get_blockchain_service(wallet.currency.network or wallet.currency.symbol)
            real_balance = service.get_balance(wallet.deposit_address)
            if wallet.balance != real_balance:
                old_balance = wallet.balance
                wallet.balance = real_balance
                wallet.save()
                logger.info(f"[BALANCE_SYNC] {wallet.currency.symbol}: {old_balance} → {real_balance}")
                synced_count += 1
        except Exception as e:
            logger.error(f"[BALANCE_SYNC] Error syncing {wallet.currency.symbol}: {e}")
            error_count += 1
    
    # ⚠️ КРИТИЧЕСКИ ВАЖНО: Синхронизируем ТОЛЬКО кошельки валют С MEMO!
    # Для валют БЕЗ MEMO баланс пользователя в БД - это зачисленные средства после консолидации,
    # а баланс на депозитном адресе - это средства, которые еще не консолидированы.
    # Синхронизация баланса пользователя с балансом депозитного адреса приведет к неправильному зачислению!
    user_wallets = UserWallet.objects.filter(
        is_system_wallet=False,
        currency__is_active=True,
        deposit_address__isnull=False,
        currency__requires_memo=True  # ⚠️ ТОЛЬКО валюты с MEMO!
    ).exclude(deposit_address='')
    
    logger.info(f"[BALANCE_SYNC] Found {user_wallets.count()} user wallets to sync (only MEMO currencies)")
    
    for wallet in user_wallets:
        try:
            service = get_blockchain_service(wallet.currency.network or wallet.currency.symbol)
            # Для TRC-20 токенов передаем contract_address при получении баланса
            contract_address = wallet.currency.contract_address if wallet.currency.network and wallet.currency.network.upper() == 'TRC20' else None
            if contract_address:
                real_balance = service.get_balance(wallet.deposit_address, contract_address=contract_address)
            else:
                real_balance = service.get_balance(wallet.deposit_address)
            
            if wallet.balance != real_balance:
                old_balance = wallet.balance
                wallet.balance = real_balance
                wallet.save()
                logger.info(f"[BALANCE_SYNC] User wallet {wallet.id} (User {wallet.user.id}, {wallet.currency.symbol}): {old_balance} → {real_balance}")
                synced_count += 1
            else:
                logger.debug(f"[BALANCE_SYNC] User wallet {wallet.id} (User {wallet.user.id}, {wallet.currency.symbol}) already in sync: {real_balance}")
                
        except Exception as e:
            logger.error(f"[BALANCE_SYNC] Error syncing user wallet {wallet.id} (User {wallet.user.id}, {wallet.currency.symbol}): {e}")
            error_count += 1
    
    logger.info(f"[BALANCE_SYNC] Balance synchronization completed. Synced: {synced_count}, Errors: {error_count}")
    return f"Synced {synced_count} wallets, {error_count} errors"
