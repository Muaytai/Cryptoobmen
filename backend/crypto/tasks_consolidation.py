"""
Задачи консолидации средств - вспомогательные функции и проверка подтверждений
"""
from __future__ import annotations
import logging
import time
from decimal import Decimal
from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from django.db import transaction
from functools import wraps
from .models import UserWallet, Cryptocurrency
from .blockchain.factory import get_blockchain_service
from transactions.models import Transaction
logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)

def retry_on_rpc_error(max_retries=3, delay=2, backoff=2):
    """
    Декоратор для повторных попыток при ошибках RPC
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_msg = str(e).lower()
                    is_rpc_error = any(keyword in error_msg for keyword in [
                        '500 server error', 'internal server error', 'connection error',
                        'timeout', 'network error', 'rpc error', 'http error'
                    ])
                    if is_rpc_error and attempt < max_retries:
                        wait_time = delay * (backoff ** attempt)
                        logger.warning(f"\033[93mRPC error on attempt {attempt + 1}/{max_retries + 1}: {e}\033[0m")
                        logger.info(f"\033[94mRetrying in {wait_time} seconds...\033[0m")
                        time.sleep(wait_time)
                        continue
                    else:
                        break
            logger.error(f"\033[91mFailed after {max_retries + 1} attempts. Last error: {last_exception}\033[0m")
            raise last_exception
        return wrapper
    return decorator

def get_min_consolidation_amount(currency: Cryptocurrency) -> Decimal:
    """Минимальная сумма для консолидации в зависимости от валюты"""
    minimums = {
        'POL': Decimal('0.01'),
        'BTC': Decimal('0.0001'),
        'ETH': Decimal('0.01'),
        'TRX': Decimal('0.01'),    # исправлено: точка
        'USDT': Decimal('0.01'),   # исправлено: точка
        'SOL': Decimal('0.01'),    # из add-solana5
    }
    return minimums.get(currency.symbol, Decimal('0.001'))

def get_gas_reserve(currency: Cryptocurrency) -> Decimal:
    """Резерв для покрытия комиссии газа в зависимости от валюты"""
    reserves = {
        'POL': Decimal('0.01'),
        'BTC': Decimal('0.00005'), 
        'ETH': Decimal('0.005'),
        'TRX': Decimal('1'),       # исправлено: 1 вместо 5
        'USDT': Decimal('0'),      # газ в TRX
        'SOL': Decimal('0.002'),   # из add-solana5
    }
    return reserves.get(currency.symbol, Decimal('0.001'))

def get_system_wallet_address(currency: Cryptocurrency) -> str:
    """Получает адрес системного кошелька для заданной валюты"""
    try:
        from .models import SystemWalletAddress
        system_wallet_address = SystemWalletAddress.objects.get(currency=currency)
        from crypto.models import GeneratedWallet
        try:
            GeneratedWallet.record_generated_wallet(
                address=system_wallet_address.address,
                private_key=system_wallet_address.private_key if hasattr(system_wallet_address, 'private_key') else 'stored_separately',
                currency=currency,
                network=currency.network,
                user=None,
                wallet_type='system',
                created_by='get_system_wallet_address',
                notes=f'System wallet for {currency.symbol}'
            )
        except Exception:
            pass
        return system_wallet_address.address
    except SystemWalletAddress.DoesNotExist:
        try:
            system_wallet = UserWallet.objects.get(
                user=None,
                currency=currency,
                is_system_wallet=True,
                is_active=True
            )
            return system_wallet.deposit_address
        except UserWallet.DoesNotExist:
            raise Exception(f"System wallet not found for {currency.symbol}")

@shared_task
def check_consolidation_confirmations():
    """
    ⚠️ КРИТИЧЕСКИ ВАЖНАЯ ФУНКЦИЯ: Проверяет подтверждения транзакций консолидации в блокчейне.
    ВАЖНО ДЛЯ АГЕНТОВ:
    После подтверждения консолидации нужно зачислить пользователю tx.amount (сумму из транзакции консолидации),
    а НЕ сумму депозита или deposit.amount - deposit.fee. 
    tx.amount содержит реальную сумму, которая была отправлена (максимально возможную).
    ИСПРАВЛЕНИЕ ЗАВИСШИХ ТРАНЗАКЦИЙ:
    - Проверяет возраст транзакций
    - Для старых транзакций (>24 часов) проверяет существование в блокчейне
    - Помечает несуществующие транзакции (>48 часов) как failed
    """
    from datetime import timedelta
    start_time = timezone.now()
    logger.info("\033[94m" + "="*60 + "\033[0m")
    logger.info("\033[94m🔍 [CONFIRMATION] Starting consolidation confirmations check...\033[0m")
    logger.info(f"\033[94m⏰ Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\033[0m")

    pending_consolidations = Transaction.objects.filter(
        type="consolidation",
        status="pending"
    )
    logger.info(f"\033[94m📋 Found {pending_consolidations.count()} pending consolidation transactions\033[0m")

    confirmed = 0
    failed_count = 0
    OLD_TRANSACTION_THRESHOLD = timedelta(hours=24)
    VERY_OLD_TRANSACTION_THRESHOLD = timedelta(hours=48)

    for tx in pending_consolidations:
        try:
            tx_age = timezone.now() - tx.timestamp
            logger.info(f"\033[94m🔍 Checking confirmation for tx: {tx.tx_hash[:16]}... ({tx.crypto.symbol}), age: {tx_age}\033[0m")

            if not tx.tx_hash:
                logger.error(f"\033[91m❌ Transaction {tx.id} has no tx_hash! Marking as failed.\033[0m")
                with transaction.atomic():
                    tx.status = "failed"
                    tx.notes = f"Transaction has no tx_hash. Original timestamp: {tx.timestamp}"
                    tx.save()
                failed_count += 1
                continue

            service = get_blockchain_service(tx.crypto.network or tx.crypto.symbol)

            # Проверка существования старых транзакций
            if tx_age > OLD_TRANSACTION_THRESHOLD:
                logger.warning(f"\033[93m⚠️ Transaction {tx.tx_hash[:16]}... is old ({tx_age}). Checking if it exists in blockchain...\033[0m")
                try:
                    @retry_on_rpc_error(max_retries=2, delay=1, backoff=1.5)
                    def check_transaction_exists():
                        if hasattr(service, 'w3') and hasattr(service.w3, 'eth'):
                            try:
                                from web3.exceptions import TransactionNotFound
                                try:
                                    tx_data = service.w3.eth.get_transaction(tx.tx_hash)
                                    return tx_data is not None
                                except TransactionNotFound:
                                    return False
                                except Exception as e:
                                    logger.warning(f"\033[93m⚠️ Error checking transaction existence: {e}\033[0m")
                                    return None
                            except ImportError:
                                try:
                                    tx_data = service.w3.eth.get_transaction(tx.tx_hash)
                                    return tx_data is not None
                                except Exception:
                                    return False
                        elif hasattr(service, '_get_transaction_by_id'):
                            try:
                                tx_data = service._get_transaction_by_id(tx.tx_hash)
                                return tx_data is not None and bool(tx_data)
                            except Exception:
                                return False
                        return None

                    exists = check_transaction_exists()
                    if tx_age > VERY_OLD_TRANSACTION_THRESHOLD and exists is False:
                        logger.error(f"\033[91m❌ Transaction {tx.tx_hash[:16]}... is very old and does not exist. Marking as failed.\033[0m")
                        with transaction.atomic():
                            tx.status = "failed"
                            tx.notes = f"Transaction not found in blockchain after {tx_age}. Original timestamp: {tx.timestamp}"
                            tx.save()
                        failed_count += 1
                        continue
                    elif exists is False:
                        logger.warning(f"\033[93m⚠️ Old transaction {tx.tx_hash[:16]}... may not exist. Will check confirmation anyway.\033[0m")
                except Exception as check_error:
                    logger.warning(f"\033[93m⚠️ Could not check transaction existence: {check_error}. Continuing...\033[0m")

            # Проверка подтверждения
            @retry_on_rpc_error(max_retries=2, delay=1, backoff=1.5)
            def check_transaction_confirmation():
                return service.is_transaction_confirmed(tx.tx_hash)
            is_confirmed = check_transaction_confirmation()
            logger.info(f"\033[94m📊 Transaction {tx.tx_hash[:16]}... confirmed: {is_confirmed}\033[0m")

            if is_confirmed:
                with transaction.atomic():
                    tx.status = "completed"
                    tx.save()

                    user_wallet = UserWallet.objects.get(
                        user=tx.user,
                        currency=tx.crypto,
                        is_system_wallet=False
                    )

                    consolidation_amount = tx.amount
                    logger.info(f"\033[94m💰 Consolidation amount (will be credited to user): {consolidation_amount} {tx.crypto.symbol}\033[0m")

                    pending_deposits = Transaction.objects.filter(
                        user=tx.user,
                        crypto=tx.crypto,
                        type="deposit",
                        status="pending"
                    )
                    logger.info(f"\033[94m📋 Found {pending_deposits.count()} pending deposits for user {tx.user.id}\033[0m")

                    # Зачисление средств и завершение депозитов
                    user_wallet.balance += consolidation_amount
                    for deposit in pending_deposits:
                        deposit.status = "completed"
                        deposit.save()
                        logger.info(f"\033[94m✅ Marked deposit {deposit.tx_hash} as completed\033[0m")

                    if consolidation_amount > 0:
                        user_wallet.save()
                        logger.info(f"\033[92m✅ Consolidation completed for user {tx.user.id}: credited {consolidation_amount} {tx.crypto.symbol}\033[0m")

                    confirmed += 1

                    # Генерация нового адреса
                    try:
                        old_address = user_wallet.deposit_address
                        if old_address:
                            blockchain_service = get_blockchain_service(tx.crypto.network or tx.crypto.symbol)
                            new_address, private_key = blockchain_service.create_new_address()
                            if not new_address or not private_key:
                                raise ValueError(f"Blockchain service returned empty address or key")
                            user_wallet.deposit_address = new_address
                            user_wallet.encrypted_private_key = private_key
                            user_wallet.save()
                            from crypto.models import GeneratedWallet
                            GeneratedWallet.record_generated_wallet(
                                address=new_address,
                                private_key=private_key,
                                currency=tx.crypto,
                                network=tx.crypto.network,
                                user=tx.user,
                                wallet_type='user',
                                created_by='check_consolidation_confirmations',
                                notes=f'Generated after consolidation for user {tx.user.id}, old address: {old_address}'
                            )
                            logger.info(f"\033[92m✅ Generated new address for user {tx.user.id}: {old_address[:10]}... -> {new_address[:10]}...\033[0m")
                    except Exception as addr_error:
                        import traceback
                        logger.error(f"\033[91m❌ Error generating new address for user {tx.user.id}: {addr_error}\033[0m")
                        logger.error(f"\033[91m❌ Traceback: {traceback.format_exc()}\033[0m")

                    # 🔹 СПЕЦИАЛЬНАЯ ЛОГИКА ДЛЯ SOL (из add-solana5)
                    if tx.crypto.symbol.upper() == 'SOL' or (tx.crypto.network or '').lower() == 'solana':
                        currency_id = tx.crypto_id
                        tx_id = tx.id
                        tx_amount = tx.amount
                        tx_symbol = tx.crypto.symbol
                        post_commit_notes = f'Consolidation confirmed: {tx_amount} {tx_symbol}, total fees: {tx.fee or 0}'
                        def _log_system_balance_after_commit():
                            try:
                                from django.db import connection
                                from .models import SystemWalletBalanceLog, Cryptocurrency
                                from .blockchain.factory import get_blockchain_service
                                from transactions.models import Transaction as TxModel
                                currency = Cryptocurrency.objects.get(id=currency_id)
                                tx_obj = TxModel.objects.get(id=tx_id)
                                svc = get_blockchain_service(currency.network or currency.symbol)
                                system_wallet_address = get_system_wallet_address(currency)
                                system_balance = svc.get_balance(system_wallet_address)
                                SystemWalletBalanceLog.log_system_wallet_balance(
                                    currency=currency,
                                    system_address=system_wallet_address,
                                    blockchain_balance=system_balance,
                                    transaction_type='consolidation',
                                    related_transaction=tx_obj,
                                    notes=post_commit_notes,
                                    sync_balance=True
                                )
                                logger.info(f"[CONSOLIDATION_CONFIRMED] Logged and synced system wallet balance for SOL: {system_balance}")
                            except Exception as log_error:
                                logger.error(f"[CONSOLIDATION_CONFIRMED] Failed to log/sync system wallet balance post-commit: {log_error}")
                        transaction.on_commit(_log_system_balance_after_commit)

        except Exception as e:
            import traceback
            logger.error(f"\033[91m❌ Error checking consolidation confirmation for {tx.tx_hash}: {e}\033[0m")
            logger.error(f"\033[91m❌ Traceback: {traceback.format_exc()}\033[0m")
            try:
                tx_age = timezone.now() - tx.timestamp
                if tx_age > VERY_OLD_TRANSACTION_THRESHOLD:
                    logger.warning(f"\033[93m⚠️ Very old transaction {tx.tx_hash[:16]}... failed to check. Marking as failed.\033[0m")
                    with transaction.atomic():
                        tx.status = "failed"
                        tx.notes = f"Failed to check confirmation after {tx_age}. Error: {str(e)}. Original timestamp: {tx.timestamp}"
                        tx.save()
                    failed_count += 1
            except Exception as mark_error:
                logger.error(f"\033[91m❌ Failed to mark transaction as failed: {mark_error}\033[0m")

    end_time = timezone.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"\033[94m" + "="*60 + "\033[0m")
    logger.info(f"\033[94m🏁 [CONFIRMATION] Process completed\033[0m")
    logger.info(f"\033[94m✅ Confirmed transactions: {confirmed}\033[0m")
    if failed_count > 0:
        logger.warning(f"\033[93m⚠️ Failed transactions: {failed_count}\033[0m")
    logger.info(f"\033[94m⏱️ Duration: {duration:.2f} seconds\033[0m")
    logger.info(f"\033[94m⏰ End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\033[0m")
    logger.info(f"\033[94m" + "="*60 + "\033[0m")
    return f"Checked consolidation confirmations: {confirmed} confirmed, {failed_count} marked as failed"

@shared_task
def consolidate_user_deposits():
    """(Полный код из master без изменений — он уже корректен и включает поддержку TRC20/USDT/BTC/Sweep и т.д.)"""
    from .models import Cryptocurrency, UserWallet, SystemWalletAddress
    processed = 0
    start_time = timezone.now()
    logger.info("\033[94m" + "="*60 + "\033[0m")
    logger.info("\033[94m🚀 [CONSOLIDATION] Starting consolidation process...\033[0m")
    logger.info(f"\033[94m⏰ Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\033[0m")

    currencies_no_memo = Cryptocurrency.objects.filter(
        is_active=True, 
        requires_memo=False
    )
    logger.info(f"\033[94m📊 Found {currencies_no_memo.count()} currencies without MEMO: {[c.symbol for c in currencies_no_memo]}\033[0m")

    for currency in currencies_no_memo:
        logger.info(f"\033[94m" + "-"*50 + "\033[0m")
        logger.info(f"\033[94m🔄 Processing consolidation for {currency.symbol} ({currency.network})\033[0m")
        try:
            system_wallet = UserWallet.objects.get(
                user=None,
                currency=currency,
                is_system_wallet=True,
                is_active=True
            )
            if not system_wallet.encrypted_private_key:
                logger.warning(f"\033[93mSystem wallet for {currency.symbol} has no private key, skipping\033[0m")
                continue

            user_wallets = UserWallet.objects.filter(
                currency=currency,
                is_system_wallet=False,
                deposit_address__isnull=False,
                encrypted_private_key__isnull=False
            ).exclude(deposit_address='')
            logger.info(f"\033[94m👥 Found {user_wallets.count()} user wallets for {currency.symbol}\033[0m")

            blockchain_service = get_blockchain_service(currency.network or currency.symbol)
            logger.info(f"\033[94m🔗 Connected to {currency.network} blockchain service\033[0m")
            currency_processed = 0

            for user_wallet in user_wallets:
                try:
                    logger.info(f"\033[94m👤 Processing user {user_wallet.user.id} wallet: {user_wallet.deposit_address[:10]}...\033[0m")
                    contract_address = currency.contract_address if currency.network and currency.network.upper() == 'TRC20' else None
                    if contract_address:
                        blockchain_balance = blockchain_service.get_balance(user_wallet.deposit_address, contract_address=contract_address)
                    else:
                        blockchain_balance = blockchain_service.get_balance(user_wallet.deposit_address)
                    logger.info(f"\033[94m💰 Blockchain balance: {blockchain_balance} {currency.symbol}\033[0m")

                    min_consolidation_amount = get_min_consolidation_amount(currency)
                    logger.info(f"\033[94m📏 Minimum threshold: {min_consolidation_amount} {currency.symbol}\033[0m")

                    if blockchain_balance < min_consolidation_amount:
                        logger.info(f"\033[93m⚠️ Balance too small for consolidation\033[0m")
                        continue

                    system_wallet_address = get_system_wallet_address(currency)

                    if hasattr(blockchain_service, 'get_max_sendable_amount'):
                        amount_to_send = blockchain_service.get_max_sendable_amount(user_wallet.deposit_address, system_wallet_address)
                        logger.info(f"\033[94m💸 Max sendable amount: {amount_to_send} {currency.symbol}\033[0m")
                    elif hasattr(blockchain_service, 'estimate_gas_fee'):
                        gas_info = blockchain_service.estimate_gas_fee(
                            to_address=system_wallet_address,
                            amount=blockchain_balance,
                            contract_address=getattr(currency, 'contract_address', None)
                        )
                        gas_cost = gas_info.get('gas_fee_eth', Decimal('0'))
                        amount_to_send = blockchain_balance - gas_cost
                        logger.info(f"\033[94m⛽ Gas cost: {gas_cost} {currency.symbol}\033[0m")
                        logger.info(f"\033[94m💸 Amount to send: {amount_to_send} {currency.symbol}\033[0m")
                    elif currency.symbol == 'BTC':
                        amount_to_send = Decimal('0')
                        logger.info(f"\033[94m💸 Bitcoin sweep mode\033[0m")
                    elif currency.network and currency.network.upper() == 'TRC20' and currency.symbol != 'TRX':
                        amount_to_send = blockchain_balance
                        logger.info(f"\033[94m💸 TRC-20 token: sending full balance\033[0m")
                    else:
                        from .gas_calculation import calculate_estimated_gas_cost
                        gas_cost = calculate_estimated_gas_cost(currency=currency, deposit_amount=blockchain_balance, user_address=user_wallet.deposit_address)
                        amount_to_send = blockchain_balance - gas_cost
                        logger.info(f"\033[94m⛽ Gas cost (estimated): {gas_cost} {currency.symbol}\033[0m")
                        logger.info(f"\033[94m💸 Amount to send: {amount_to_send} {currency.symbol}\033[0m")

                    if amount_to_send <= 0 and currency.symbol != 'BTC':
                        logger.warning(f"\033[93m⚠️ Amount to send is zero or negative\033[0m")
                        continue

                    logger.info(f"\033[94m🚀 Consolidating {amount_to_send} {currency.symbol} to system wallet\033[0m")

                    # TRC-20: проверка TRX для bandwidth
                    if currency.network and currency.network.upper() == 'TRC20' and currency.symbol != 'TRX':
                        trx_balance = blockchain_service.get_balance(user_wallet.deposit_address)
                        min_trx_for_bandwidth = Decimal('2')
                        if trx_balance < min_trx_for_bandwidth:
                            logger.warning(f"\033[93m⚠️ Insufficient TRX for bandwidth\033[0m")
                            try:
                                trx_currency = Cryptocurrency.objects.get(symbol='TRX', network='TRC20')
                                try:
                                    system_trx_wallet = SystemWalletAddress.objects.get(currency=trx_currency)
                                    system_trx_address = system_trx_wallet.address
                                    system_trx_private_key = system_trx_wallet.private_key if hasattr(system_trx_wallet, 'private_key') else None
                                    if not system_trx_private_key:
                                        system_trx_wallet_user = UserWallet.objects.get(
                                            user=None,
                                            currency=trx_currency,
                                            is_system_wallet=True,
                                            is_active=True
                                        )
                                        system_trx_private_key = system_trx_wallet_user.encrypted_private_key
                                        system_trx_address = system_trx_wallet_user.deposit_address
                                    trx_amount_to_send = min_trx_for_bandwidth - trx_balance
                                    logger.info(f"\033[94m📤 Sending {trx_amount_to_send} TRX for bandwidth\033[0m")
                                    @retry_on_rpc_error(max_retries=2, delay=1, backoff=1.5)
                                    def send_trx_for_bandwidth():
                                        return blockchain_service.send_transaction(
                                            private_key=system_trx_private_key,
                                            to_address=user_wallet.deposit_address,
                                            amount=trx_amount_to_send,
                                            memo=""
                                        )
                                    gas_tx_hash = send_trx_for_bandwidth()
                                    logger.info(f"\033[92m✅ TRX sent for bandwidth: {gas_tx_hash}\033[0m")
                                    time.sleep(10)
                                except (SystemWalletAddress.DoesNotExist, UserWallet.DoesNotExist) as e:
                                    logger.error(f"\033[91m❌ System TRX wallet not found: {e}\033[0m")
                                    continue
                            except Exception as trx_error:
                                logger.error(f"\033[91m❌ Error sending TRX for bandwidth: {trx_error}\033[0m")
                                continue

                    # Валидация Bitcoin адреса
                    if currency.symbol == 'BTC':
                        if '_' in system_wallet_address or not system_wallet_address.startswith(('1', '3', 'bc1', 'tb1')):
                            logger.error(f"\033[91m❌ Invalid Bitcoin system wallet address: {system_wallet_address}\033[0m")
                            continue

                    contract_address_for_send = currency.contract_address if currency.network and currency.network.upper() == 'TRC20' else None

                    @retry_on_rpc_error(max_retries=3, delay=2, backoff=2)
                    def send_consolidation_transaction():
                        return blockchain_service.send_transaction(
                            private_key=user_wallet.encrypted_private_key,
                            to_address=system_wallet_address,
                            amount=amount_to_send,
                            memo=f"consolidation_{user_wallet.user_id}",
                            contract_address=contract_address_for_send
                        )

                    tx_hash = send_consolidation_transaction()
                    logger.info(f"\033[92m✅ Transaction sent: {tx_hash}\033[0m")

                    consolidation_amount_to_save = amount_to_send if currency.symbol != 'BTC' else blockchain_balance
                    with transaction.atomic():
                        Transaction.objects.create(
                            user=user_wallet.user,
                            crypto=currency,
                            amount=consolidation_amount_to_save,
                            tx_hash=tx_hash,
                            type="consolidation",
                            status="pending",
                            timestamp=timezone.now()
                        )

                    processed += 1
                    currency_processed += 1
                    logger.info(f"\033[92m💾 Consolidation saved to DB: {tx_hash}\033[0m")
                    logger.info(f"\033[92m🎉 Consolidated {consolidation_amount_to_save} {currency.symbol} for user {user_wallet.user.id}\033[0m")

                except Exception as e:
                    logger.error(f"\033[91m❌ Error consolidating {currency.symbol} for user {user_wallet.user_id}: {e}\033[0m")
                    continue

            logger.info(f"\033[94m📈 Currency {currency.symbol} summary: {currency_processed} processed\033[0m")

        except UserWallet.DoesNotExist:
            logger.warning(f"\033[93m⚠️ System wallet for {currency.symbol} not found\033[0m")
            continue
        except Exception as e:
            logger.error(f"\033[91m❌ Error processing currency {currency.symbol}: {e}\033[0m")
            continue

    end_time = timezone.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"\033[94m" + "="*60 + "\033[0m")
    logger.info(f"\033[94m🏁 [CONSOLIDATION] Process completed\033[0m")
    logger.info(f"\033[94m📊 Total transactions processed: {processed}\033[0m")
    logger.info(f"\033[94m⏱️ Duration: {duration:.2f} seconds\033[0m")
    logger.info(f"\033[94m⏰ End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\033[0m")
    logger.info(f"\033[94m" + "="*60 + "\033[0m")
    return f"Consolidation completed: {processed} transactions"