
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
    cache_key = current_time // cache_seconds  # Группируем по временным интервалам
    
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
        
        # Проверяем доступность сервиса с кэшированием через батч-процессор
        balance = cached_batch_processor.get_cached_balance(service, address)
        if balance == 0:
            logger.debug(f"[PARALLEL] Zero balance for {address}, skipping")
            return (address, [], False)
        
        # Получаем транзакции
        if currency.symbol == 'POL':
            # Для Polygon используем оптимизированный сканер с кэшированием
            current_block = service.w3.eth.block_number
            from_block = max(current_block - 500, 1)
            logger.info(f"[PARALLEL][POL] Optimized scan: blocks {from_block} to {current_block} for {address}")
            
            # Используем оптимизированный сканер если доступен
            if hasattr(service, 'optimized_scanner') and service.optimized_scanner:
                raw_transactions = service.optimized_scanner.scan_optimized(
                    [address], from_block, current_block
                )
            else:
                # Fallback к обычному сканированию
                raw_transactions = service.get_transactions(
                    address=address,
                    from_block=from_block,
                    to_block=current_block
                )
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
    Обрабатывает множество адресов одной валюты батчами для повышения эффективности
    """
    logger.info(f"[BATCH] Starting batch processing for {len(user_wallets)} addresses of {currency.symbol}")
    
    # Сначала получаем все балансы одним батчем
    addresses = [wallet.deposit_address for wallet in user_wallets]
    address_to_wallet = {wallet.deposit_address: wallet for wallet in user_wallets}
    
    # Получаем балансы всех адресов батчем
    balances = cached_batch_processor.batch_get_balances_cached(service, addresses)
    
    # Фильтруем адреса с ненулевыми балансами
    active_addresses = []
    transaction_params = []
    
    for address, balance in balances.items():
        if balance > 0:
            wallet = address_to_wallet[address]
            
            # Получаем последнюю транзакцию для расчёта min_timestamp
            from transactions.models import Transaction
            last_tx = Transaction.objects.filter(
                user=wallet.user,
                crypto=currency,
                tx_hash__isnull=False
            ).order_by("-timestamp").first()
            min_ts = int(last_tx.timestamp.timestamp() * 1000) if last_tx else 0
            
            active_addresses.append(address)
            
            # Подготавливаем параметры для get_transactions
            if currency.symbol == 'POL':
                current_block = service.w3.eth.block_number
                from_block = max(current_block - 500, 1)
                params = {'from_block': from_block, 'to_block': current_block}
            elif currency.network and currency.network.upper() == 'ERC20':
                params = {'min_timestamp': min_ts, 'contract_address': currency.contract_address}
            else:
                params = {'min_timestamp': min_ts}
            
            transaction_params.append((address, params))
    
    logger.info(f"[BATCH] Found {len(active_addresses)} addresses with balance > 0 for {currency.symbol}")
    
    results = {}
    
    if transaction_params:
        # Получаем транзакции для всех активных адресов батчем
        if currency.symbol == 'POL' and hasattr(service, 'optimized_scanner') and service.optimized_scanner:
            # Для POL используем оптимизированный сканер для всех адресов сразу
            logger.info(f"[BATCH][POL] Using optimized scanner for {len(active_addresses)} addresses")
            current_block = service.w3.eth.block_number
            from_block = max(current_block - 500, 1)
            
            try:
                all_transactions = service.optimized_scanner.scan_optimized(
                    active_addresses, from_block, current_block
                )
                
                # Группируем транзакции по адресам
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
                # Fallback к обычному батч-процессору
                all_transactions = cached_batch_processor.batch_get_transactions(service, transaction_params)
                for address, txs in all_transactions.items():
                    results[address] = (txs, True)
        else:
            # Для других валют используем обычный батч-процессор
            all_transactions = cached_batch_processor.batch_get_transactions(service, transaction_params)
            for address, txs in all_transactions.items():
                results[address] = (txs, True)
    
    # Добавляем адреса с нулевым балансом
    for address in addresses:
        if address not in results:
            results[address] = ([], False)
    
    logger.info(f"[BATCH] Completed batch processing for {currency.symbol}: {len(results)} addresses processed")
    return results


@shared_task
@single_instance_task(timeout=300)  # 5 минут блокировка
def check_blockchain_deposits():
    """
    Периодическая задача для проверки новых депозитов в блокчейне.
    """
    from transactions.models import Transaction
    from .models import SystemWalletAddress, UserDepositMemo, UserWallet
    processed = 0
    logger.info("[check_blockchain_deposits] Starting deposit check...")

    # Обрабатываем все системные кошельки
    for wallet in SystemWalletAddress.objects.select_related('currency').all():
        currency = wallet.currency
        if not currency.is_active:
            continue
        if not getattr(currency, 'requires_memo', False):
            logger.info(f"Skipping {currency.symbol} in {wallet.network}: MEMO not required (per official docs). Currency decimals: {currency.decimals}")
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
            memo = ev.get("memo", "")
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
                # Для валют без memo (как BNB) - ищем пользователя по адресу депозита
                # В BSC/BEP20 нет memo, поэтому нужно найти пользователя по адресу кошелька
                try:
                    # Ищем пользователя, у которого deposit_address совпадает с адресом отправителя
                    from_address = ev.get("from_address", "")
                    if from_address:
                        user_wallet = UserWallet.objects.filter(
                            deposit_address__iexact=from_address,
                            currency=wallet.currency
                        ).first()
                        if user_wallet and user_wallet.user:
                            user = user_wallet.user
                            logger.info(f"Found user {user.id} by deposit address {from_address}")
                        else:
                            logger.warning(f"No user found for deposit address {from_address}. Skipping.")
                            continue
                    else:
                        logger.warning(f"No from_address in transaction {tx_hash}. Skipping.")
                        continue
                except Exception as e:
                    logger.error(f"Error while finding user by deposit address: {e}", exc_info=True)
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
                    # Проверяем, что транзакция с таким hash еще не существует
                    if Transaction.objects.filter(tx_hash=tx_hash).exists():
                        logger.warning(f"[memo] Transaction {tx_hash} already exists, skipping duplicate")
                        continue
                        
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

    # 2. Теперь обрабатываем валюты без MEMO/tag по уникальным адресам пользователей с батч-обработкой
    currencies_no_memo = Cryptocurrency.objects.filter(is_active=True, requires_memo=False)
    
    for currency in currencies_no_memo:
        logger.info(f"[BATCH] Starting batch processing for {currency.symbol}, network={currency.network}, decimals={currency.decimals}, requires_memo={currency.requires_memo}")
        
        user_wallets = UserWallet.objects.filter(
            currency=currency, 
            is_system_wallet=False, 
            deposit_address__isnull=False
        ).exclude(deposit_address='')
        
        if not user_wallets.exists():
            logger.info(f"[BATCH] No user wallets found for {currency.symbol}")
            continue
        
        try:
            service = get_blockchain_service(currency.network or currency.symbol)
            
            # Используем батч-обработку для эффективного сканирования
            batch_results = process_addresses_batch(currency, user_wallets, service)
            
            # Создаём маппинг адресов к кошелькам
            address_to_wallet = {wallet.deposit_address: wallet for wallet in user_wallets}
            
            # Обрабатываем результаты батча
            for address, (raw_transactions, success) in batch_results.items():
                if not success or not raw_transactions:
                    continue
                
                user_wallet = address_to_wallet.get(address)
                if not user_wallet:
                    continue
                
                logger.info(f"[BATCH] Processing {len(raw_transactions)} transactions for address {address}")
                
                # Обрабатываем найденные транзакции
                for ev in raw_transactions:
                    tx_hash = ev.get("transaction_id")
                    amount_str = ev.get("value")
                    logger.info(f"[BATCH] Processing: {currency.symbol} {address} tx={tx_hash} amount={amount_str}")
                    existing_tx = Transaction.objects.filter(tx_hash=tx_hash, user=user_wallet.user).first()
                    if existing_tx:
                        logger.warning(f"[BATCH] Duplicate tx {tx_hash} for user {user_wallet.user.id}. Re-sending signal.")
                        # Повторно отправляем сигнал, если транзакция уже существует
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
                                        "amount": str(existing_tx.amount),
                                    }
                                }
                            )
                            logger.info(f"[BATCH] Re-sent WebSocket signal for address {address}")
                        except Exception as e:
                            logger.error(f"[BATCH] Failed to re-send WebSocket signal for address {address}: {e}")
                        continue
                    
                    try:
                        # Логируем входные данные для диагностики
                        logger.info(f"[BATCH] Processing amount conversion: currency={currency.symbol}, network={currency.network}, amount_str={amount_str}, decimals={currency.decimals}")
                        
                        # Проверяем, является ли amount_str уже конвертированной суммой (от оптимизированного сканера)
                        # Если в amount_str есть точка и число меньше 1000, скорее всего это уже готовая сумма
                        is_already_converted = (
                            '.' in amount_str and 
                            Decimal(amount_str) < Decimal('1000') and
                            currency.symbol == 'POL'
                        )
                        
                        if is_already_converted:
                            # Данные уже в POL (от оптимизированного сканера)
                            amount = Decimal(amount_str)
                            logger.info(f"[BATCH][OPTIMIZED] Amount already converted by optimized scanner: {amount} {currency.symbol}")
                        elif currency.network and currency.network.upper() == 'ERC20':
                            if currency.symbol == 'ETH':
                                # ETH в Wei (18 decimals)
                                amount = Decimal(amount_str) / Decimal(10**18)
                                logger.info(f"[BATCH] ETH: Converting {amount_str} Wei to {amount} ETH")
                            else:
                                # ERC-20 токены используют свои decimals
                                amount = Decimal(amount_str) / Decimal(10**currency.decimals)
                                logger.info(f"[BATCH] ERC20: Converting {amount_str} with {currency.decimals} decimals to {amount} {currency.symbol}")
                        else:
                            # Остальные валюты используют свои decimals (Wei формат)
                            amount = Decimal(amount_str) / Decimal(10**currency.decimals)
                            logger.info(f"[BATCH] Converting {amount_str} Wei with {currency.decimals} decimals to {amount} {currency.symbol}")
                        
                        # Логируем результат
                        logger.info(f"[BATCH] Amount conversion result: {amount} {currency.symbol}")
                        
                    except (ValueError, TypeError) as e:
                        logger.error(f"[BATCH] Invalid amount: {amount_str}, error: {e}")
                        continue
                        
                    # Проверяем, что транзакция с таким hash еще не существует
                    if Transaction.objects.filter(tx_hash=tx_hash).exists():
                        logger.warning(f"[BATCH] Transaction {tx_hash} already exists, skipping duplicate")
                        continue
                        
                    with transaction.atomic():
                        user_wallet.balance += amount
                        user_wallet.save()
                        
                        # Детальное логирование перед сохранением
                        logger.info(f"[BATCH] Saving transaction: user={user_wallet.user.id}, currency={currency.symbol}, amount={amount}, tx_hash={tx_hash}")
                        
                        Transaction.objects.create(
                            user=user_wallet.user,
                            crypto=currency,
                            amount=amount,
                            tx_hash=tx_hash,
                            type="deposit",
                            status="completed",
                            timestamp=timezone.now()
                        )
                        processed += 1
                        logger.info(f"[BATCH] Deposit credited: {user_wallet.user} {currency.symbol} {amount}")

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
                        logger.info(f"[BATCH] WebSocket signal sent for address {address}")
                    except Exception as e:
                        logger.error(f"[BATCH] Failed to send WebSocket signal for address {address}: {e}")
                    
                    # Агрегируем на системном кошельке (балансовый учёт платформы)
                    system_wallet_balance, _ = UserWallet.objects.get_or_create(
                        user=None,
                        currency=currency,
                        defaults={'balance': Decimal('0'), 'is_system_wallet': True, 'is_active': True}
                    )
                    system_wallet_balance.balance += amount
                    system_wallet_balance.save()
                    
                    # Для BNB/BEP20 выполняем немедленную консолидацию (свип) на системный адрес
                    if currency.symbol.upper() == 'BNB':
                        try:
                            system_addr_model = SystemWalletAddress.objects.filter(currency=currency).first()
                            if system_addr_model and user_wallet.encrypted_private_key:
                                current_balance = service.get_balance(user_wallet.deposit_address)
                                sweep_reserve = Decimal('0.00005')  # запас на газ
                                if current_balance > sweep_reserve:
                                    sweep_amount = current_balance - sweep_reserve
                                    tx_sweep = service.send_transaction(
                                        private_key=user_wallet.encrypted_private_key,
                                        to_address=system_addr_model.address,
                                        amount=sweep_amount,
                                    )
                                    logger.info(f"[BNB][SWEEP] {sweep_amount} BNB from {user_wallet.deposit_address} -> {system_addr_model.address}, tx={tx_sweep}")
                        except Exception as e:
                            logger.warning(f"[BNB][SWEEP] failed for {user_wallet.deposit_address}: {e}")

                    # Для POL запускаем немедленную консолидацию после депозита
                    if currency.symbol == 'POL':
                        logger.info(f"[POL] Triggering immediate consolidation after deposit for user {user_wallet.user.id}")
                        from .tasks_consolidation import consolidate_user_deposits
                        
                        # Проверяем доступность Celery worker'ов для POL
                        try:
                            from celery import current_app
                            inspect = current_app.control.inspect()
                            active_workers = inspect.active()
                            
                            if active_workers and any(active_workers.values()):
                                # Есть активные worker'ы - запускаем асинхронно
                                consolidate_user_deposits.delay()
                                logger.info("[POL] Consolidation task queued after deposit via Celery")
                            else:
                                # Нет worker'ов - запускаем синхронно
                                logger.warning("[POL] No active Celery workers, running consolidation synchronously")
                                result = consolidate_user_deposits()
                                logger.info(f"[POL] Sync consolidation after deposit: {result}")
                                
                        except Exception as e:
                            logger.warning(f"[POL] Celery check failed, running sync consolidation: {e}")
                            try:
                                result = consolidate_user_deposits()
                                logger.info(f"[POL] Sync consolidation after deposit: {result}")
                            except Exception as sync_e:
                                logger.error(f"[POL] Sync consolidation failed: {sync_e}")

                    # Ротация депозитного адреса после успешного зачисления
                    try:
                        new_address, new_private_key = service.create_new_address(user_id=user_wallet.user.id)
                        user_wallet.deposit_address = new_address
                        user_wallet.encrypted_private_key = new_private_key
                        user_wallet.save(update_fields=["deposit_address", "encrypted_private_key", "updated_at"]) if hasattr(user_wallet, "updated_at") else user_wallet.save()

                        # Сообщим фронту о новом адресе (опционально)
                        try:
                            channel_layer = get_channel_layer()
                            async_to_sync(channel_layer.group_send)(
                                f"deposit_address_{address}",
                                {
                                    "type": "deposit_status_update",
                                    "data": {
                                        "address": new_address,
                                        "currency": currency.symbol,
                                        "network": currency.network,
                                        "status": "rotated",
                                    },
                                },
                            )
                        except Exception:
                            pass
                        logger.info(f"[BATCH] Deposit processed for user {user_wallet.user_id}")
                    except Exception as e:
                        logger.error(f"[BATCH] Failed to rotate address for user {user_wallet.user_id}: {e}")
            
        except Exception as e:
            logger.error(f"[BATCH] Error processing currency {currency.symbol}: {e}")
            continue
        
        # Очищаем кэш периодически
        try:
            cached_batch_processor.cleanup_cache()
        except Exception as cache_error:
            logger.warning(f"[BATCH] Cache cleanup failed: {cache_error}")

    # --- XRP Ledger ---
    xrp_wallets = SystemWalletAddress.objects.filter(network__iexact="XRP", currency__is_active=True)
    logger.info(f"[check_blockchain_deposits] Found {xrp_wallets.count()} XRP wallets to check")
    for wallet in xrp_wallets:
        try:
            logger.info(f"[check_blockchain_deposits][XRP] Checking wallet: {wallet.address} for currency {wallet.currency.symbol}")
            # Получаем последние обработанные транзакции (можно доработать для оптимизации)
            last_tx = Transaction.objects.filter(crypto=wallet.currency, tx_hash__isnull=False).order_by("-timestamp").first()
            # XRP Ledger не использует timestamp, а ledger index. Для простоты пока не фильтруем по ledger.
            service = XRPService()
            incoming_txs = service.get_transactions(wallet.address)
            logger.info(f"[check_blockchain_deposits][XRP] Found {len(incoming_txs)} incoming payments for {wallet.address}")
            for ev in incoming_txs:
                memo = ev.get("memo")
                tx_hash = ev.get("transaction_id")
                amount_str = ev.get("value")

                logger.info(f"[XRP][DEPOSIT] Processing Event: tx_hash={tx_hash}, memo='{memo}', amount='{amount_str}', ev={ev}")

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
                    logger.warning(f"Skipping event for {wallet.currency.symbol} because it requires a memo, but none was provided. ev={ev}")
                    continue
                
                else:
                    # Если memo не обязателен и его нет (например, BTC)
                    # TODO: Реализовать логику для валют без memo (поиск по уникальному адресу)
                    logger.info(f"Skipping deposit for {wallet.currency.symbol} as it does not require memo and no memo was provided (logic not implemented). ev={ev}")
                    continue

                if not user:
                    logger.warning(f"User not found for transaction {tx_hash}. Skipping.")
                    continue

                # Проверяем на дубликат ДО основной логики
                if Transaction.objects.filter(tx_hash=tx_hash).exists():
                    logger.warning(f"[XRP] Duplicate transaction found: tx_hash={tx_hash}. Skipping.")
                    continue
                deposit_memo = UserDepositMemo.objects.filter(memo=memo, status="waiting").first()
                if not deposit_memo:
                    logger.warning(f"[XRP] No waiting UserDepositMemo found for tag='{memo}'.")
                    continue

                # ВЫЧИСЛЯЕМ amount перед использованием!
                try:
                    decimals = getattr(wallet.currency, "decimals", 6) or 6
                    amount = Decimal(amount_str) / Decimal(10 ** decimals)
                except (ValueError, TypeError, AttributeError) as e:
                    logger.error(f"Invalid amount format: {amount_str}. Skipping. Error: {e}")
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
                    # Проверяем, что транзакция с таким hash еще не существует
                    if Transaction.objects.filter(tx_hash=tx_hash).exists():
                        logger.warning(f"[XRP] Transaction {tx_hash} already exists, skipping duplicate")
                        continue
                        
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
                    logger.info(f"[XRP] Successfully processed deposit for tag='{memo}', tx_hash={tx_hash}")
        except Exception as e:
            logger.error(f"[XRP] Error processing wallet {wallet.address}: {e}", exc_info=True)

    logger.info(f"Finished deposit check. Processed {processed} transactions.")
    
    # Если были обработаны новые депозиты, запускаем задачу их консолидации
    if processed > 0:
        logger.info("Triggering process_pending_deposits to handle consolidation...")
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
        logger.error(f"Withdrawal with id {withdrawal_id} not found. The task will not be executed.")
        return f"error:not_found"

    try:
        # Используем одну транзакцию БД для всех проверок и начальных изменений
        with transaction.atomic():
            # Перезагружаем объект внутри транзакции для безопасности
            withdrawal = Withdrawal.objects.select_for_update().get(id=withdrawal_id)

            # Проверяем только, что email подтвержден
            if not withdrawal.is_email_confirmed:
                logger.warning(f"Withdrawal {withdrawal_id} email is not confirmed. Status: {withdrawal.transaction.status}")
                return f"skip:not_confirmed"
            
            # КРИТИЧЕСКАЯ ПРОВЕРКА: не обрабатывать уже отправленные или завершенные
            if withdrawal.transaction.status in ['awaiting_confirmation', 'completed', 'failed']:
                if withdrawal.transaction.tx_hash:
                    logger.warning(f"Withdrawal {withdrawal_id} already processed with tx_hash: {withdrawal.transaction.tx_hash}. Status: {withdrawal.transaction.status}. Skipping to avoid duplication.")
                    return f"skip:already_processed:{withdrawal.transaction.status}"
                elif withdrawal.transaction.status == 'failed':
                    logger.warning(f"Withdrawal {withdrawal_id} already failed. Status: {withdrawal.transaction.status}. Skipping.")
                    return f"skip:already_failed"

            crypto = withdrawal.transaction.crypto
            amount_to_send = withdrawal.transaction.amount
            commission = withdrawal.transaction.fee
            total_amount = amount_to_send + commission
            
            # --- Проверка баланса пользователя ---
            user_wallet = UserWallet.objects.select_for_update().get(id=withdrawal.wallet.id)
            if user_wallet.balance < total_amount:
                withdrawal.transaction.status = 'failed'
                withdrawal.transaction.notes = "Insufficient funds at the time of processing."
                withdrawal.transaction.save()
                logger.error(f"Insufficient funds for withdrawal {withdrawal.id}. Balance: {user_wallet.balance}, required: {total_amount}")
                return "error:insufficient_funds"

            # Блокируем средства на балансе пользователя
            user_wallet.balance -= total_amount
            user_wallet.locked_balance += total_amount
            user_wallet.save()

            # Меняем статус на "в обработке" перед отправкой в сеть
            withdrawal.transaction.status = 'processing'
            withdrawal.transaction.save()
            
            # Создаем Transfer объект если он еще не существует
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
            if created:
                logger.info(f"Created new Transfer {transfer.id} for withdrawal {withdrawal.id}")

        # --- Отправка в блокчейн (вне транзакции БД) ---
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
        
        if network.upper() == 'ERC20' or network.upper() == 'TRC20':
            tx_kwargs['contract_address'] = crypto.contract_address

        tx_hash = service.send_transaction(**tx_kwargs)

        # --- Финализация в БД после успешной отправки ---
        with transaction.atomic():
            # Обновляем основную транзакцию
            withdrawal.transaction.tx_hash = tx_hash
            withdrawal.transaction.status = 'awaiting_confirmation'
            withdrawal.transaction.save()

            # --- Начисление комиссии на внутренний кошелек ---
            commission_wallet, _ = CommissionWallet.objects.get_or_create(currency=crypto)
            commission_wallet.balance += commission
            commission_wallet.save()

            # --- Логирование транзакции комиссии ---
            CommissionTransaction.objects.create(
                user=withdrawal.user,
                currency=crypto,
                amount=commission,
                commission_type='withdraw',
                related_object_id=str(withdrawal.transaction.transaction_id)
            )

        # Запускаем отложенную задачу для проверки подтверждения
        check_withdrawal_confirmation.apply_async(args=[withdrawal.id], countdown=60)

        logger.info(f"Withdrawal {withdrawal.id} sent to blockchain with tx_hash: {tx_hash}. Commission: {commission}. Awaiting confirmation.")
        return f"success:sent_to_network:{tx_hash}"

    except Exception as e:
        logger.error(f"!!! Caught exception for withdrawal {withdrawal_id} !!!", exc_info=True)
        logger.error(f"Transaction failed for withdrawal {withdrawal_id}: {e}", exc_info=True)
        if withdrawal:
            with transaction.atomic():
                # Перезагружаем объекты для безопасности
                withdrawal_to_fail = Withdrawal.objects.select_for_update().get(id=withdrawal_id)
                user_wallet_to_refund = UserWallet.objects.select_for_update().get(id=withdrawal_to_fail.wallet.id)

                amount_to_refund = withdrawal_to_fail.transaction.amount + withdrawal_to_fail.transaction.fee

                # Проверяем, есть ли что возвращать
                if user_wallet_to_refund.locked_balance >= amount_to_refund:
                    user_wallet_to_refund.locked_balance -= amount_to_refund
                    user_wallet_to_refund.balance += amount_to_refund
                    user_wallet_to_refund.save()
                    
                    withdrawal_to_fail.transaction.status = 'failed'
                    withdrawal_to_fail.transaction.notes = f"Transaction error: {str(e)}. Funds refunded."
                    withdrawal_to_fail.transaction.save()
                else:
                    # На случай, если что-то пошло совсем не так
                    withdrawal_to_fail.transaction.status = 'failed'
                    withdrawal_to_fail.transaction.notes = f"Transaction error: {str(e)}. Refund failed due to inconsistent locked balance."
                    withdrawal_to_fail.transaction.save()

        return f"error:transaction_failed - {str(e)}"


@shared_task
def process_pending_withdrawals():
    """
    Периодическая задача для обработки всех ожидающих или зависших заявок на вывод.
    Находит выводы, которые подтверждены по email, но не завершены,
    и перезапускает для них задачу обработки.
    Также находит выводы со статусом 'awaiting_confirmation', которые подтверждены
    по email и администратором, и запускает для них задачу проверки подтверждения в блокчейне.
    """
    from transactions.models import Withdrawal
    from django.db.models import Q

    # Найдем зависшие выводы (pending или processing) с подтвержденным email
    # НО исключаем те, у которых УЖЕ есть tx_hash (чтобы не дублировать отправки)
    stuck_withdrawals = Withdrawal.objects.filter(
        Q(transaction__status='pending') | Q(transaction__status='processing'),
        is_email_confirmed=True,
        transaction__tx_hash__isnull=True  # ТОЛЬКО без tx_hash!
    )
    
    logger.info(f"Found {stuck_withdrawals.count()} stuck withdrawals to process.")

    for withdrawal in stuck_withdrawals:
        logger.info(f"Re-queueing processing for withdrawal {withdrawal.id}")
        process_withdrawal.delay(withdrawal.id)

    # Найдем выводы, которые находятся в статусе 'awaiting_confirmation' (убрали требование confirmed_by_admin)
    awaiting_confirmation_withdrawals = Withdrawal.objects.filter(
        transaction__status='awaiting_confirmation',
        is_email_confirmed=True
    )
    
    logger.info(f"Found {awaiting_confirmation_withdrawals.count()} awaiting confirmation withdrawals to check blockchain confirmation.")

    for withdrawal in awaiting_confirmation_withdrawals:
        logger.info(f"Queueing blockchain confirmation check for withdrawal {withdrawal.id}")
        check_withdrawal_confirmation.delay(withdrawal.id)

def process_consolidation_for_wallet(args: Tuple) -> Tuple[bool, str, Decimal]:
    """Обрабатывает консолидацию для одного кошелька в параллельном потоке"""
    (currency, user_wallet, blockchain_service, system_wallet_address, min_threshold) = args
    
    try:
        # Проверяем реальный баланс в блокчейне с кэшированием через батч-процессор
        blockchain_balance = cached_batch_processor.get_cached_balance(blockchain_service, user_wallet.deposit_address)
        
        if blockchain_balance < min_threshold:
            logger.debug(f"[CONSOLIDATION] Address {user_wallet.deposit_address} has {blockchain_balance} {currency.symbol}, less than minimum {min_threshold}")
            return (False, user_wallet.deposit_address, Decimal('0'))
        
        logger.info(f"[CONSOLIDATION] Found {blockchain_balance} {currency.symbol} on address {user_wallet.deposit_address} for user {user_wallet.user.id}")
        
        # Рассчитываем максимальную отправляемую сумму
        if hasattr(blockchain_service, 'get_max_sendable_amount'):
            # Для POL используем умный расчёт газа
            amount_to_send = blockchain_service.get_max_sendable_amount(
                user_wallet.deposit_address, 
                system_wallet_address
            )
            if amount_to_send <= 0:
                logger.warning(f"[CONSOLIDATION] Cannot consolidate for user {user_wallet.user.id}: insufficient balance after gas deduction")
                return (False, user_wallet.deposit_address, Decimal('0'))
            logger.info(f"[CONSOLIDATION] Smart gas calculation: sending {amount_to_send} {currency.symbol}")
        else:
            # Fallback для других валют
            gas_reserve = get_gas_reserve(currency)
            amount_to_send = blockchain_balance - gas_reserve
            if amount_to_send <= 0:
                logger.warning(f"[CONSOLIDATION] Cannot consolidate for user {user_wallet.user.id}: insufficient balance after gas reserve")
                return (False, user_wallet.deposit_address, Decimal('0'))
            logger.info(f"[CONSOLIDATION] Fixed gas reserve: sending {amount_to_send} {currency.symbol}")
        
        # Выполняем консолидацию
        logger.info(f"[CONSOLIDATION] Consolidating {amount_to_send} {currency.symbol} from {user_wallet.deposit_address} to system wallet")
        
        tx_hash = blockchain_service.send_transaction(
            private_key=user_wallet.encrypted_private_key,
            to_address=system_wallet_address,
            amount=amount_to_send,
        )
        
        logger.info(f"[CONSOLIDATION] Transaction sent: {tx_hash}")
        return (True, tx_hash, amount_to_send)
        
    except Exception as e:
        logger.error(f"[CONSOLIDATION] Error processing wallet {user_wallet.deposit_address}: {e}")
        return (False, user_wallet.deposit_address, Decimal('0'))

@shared_task
def process_pending_deposits():
    """
    Обрабатывает только что зачисленные депозиты и выполняет их консолидацию с многопоточностью.
    Эта задача запускается после check_blockchain_deposits, когда депозиты уже в БД.
    """
    from django.utils import timezone
    from datetime import timedelta
    from django.db import transaction as db_transaction
    from .tasks_consolidation import get_min_consolidation_amount, get_gas_reserve, get_system_wallet_address
    from .blockchain.factory import get_blockchain_service
    
    logger.info("🔄 Processing pending deposits for consolidation with parallel processing...")
    
    from transactions.models import Transaction
    from crypto.models import Cryptocurrency, UserWallet
    
    # Получаем валюты, которые НЕ требуют мемо (они нуждаются в консолидации)
    no_memo_currencies = Cryptocurrency.objects.filter(requires_memo=False, is_active=True)
    consolidated_count = 0
    
    for currency in no_memo_currencies:
        logger.info(f"[CONSOLIDATION] Processing {currency.symbol} with parallel processing...")
        
        try:
            # Получаем сервис блокчейна
            blockchain_service = get_blockchain_service(currency.network or currency.symbol)
            
            # Проверяем доступность сервиса
            try:
                system_wallet_address = get_system_wallet_address(currency)
                test_balance = cached_batch_processor.get_cached_balance(blockchain_service, system_wallet_address)
                logger.debug(f"Service for {currency.symbol} is available. System balance: {test_balance}")
            except Exception as e:
                logger.error(f"Service not available for {currency.symbol}: {e}. Skipping.")
                continue
            
            # Ищем кошельки пользователей с балансом на блокчейне
            user_wallets_with_funds = UserWallet.objects.filter(
                currency=currency,
                is_system_wallet=False,
                deposit_address__isnull=False
            ).exclude(deposit_address='')
            
            if not user_wallets_with_funds.exists():
                logger.info(f"[CONSOLIDATION] No user wallets found for {currency.symbol}")
                continue
            
            min_threshold = get_min_consolidation_amount(currency)
            
            # Подготавливаем аргументы для параллельной обработки
            consolidation_args = []
            for user_wallet in user_wallets_with_funds:
                consolidation_args.append((currency, user_wallet, blockchain_service, system_wallet_address, min_threshold))
            
            logger.info(f"[CONSOLIDATION] Processing {len(consolidation_args)} wallets for {currency.symbol} in parallel")
            
            # Выполняем параллельную консолидацию
            max_workers = min(5, len(consolidation_args))  # Ограничиваем количество потоков для консолидации
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Запускаем задачи консолидации
                future_to_wallet = {
                    executor.submit(process_consolidation_for_wallet, args): args[1] 
                    for args in consolidation_args
                }
                
                # Собираем результаты
                for future in as_completed(future_to_wallet):
                    user_wallet = future_to_wallet[future]
                    try:
                        success, tx_hash_or_address, amount_sent = future.result(timeout=120)  # Увеличенный таймаут для консолидации
                        
                        if not success:
                            continue
                        
                        tx_hash = tx_hash_or_address
                        amount_to_send = amount_sent
                        
                        # Проверяем, что транзакция ещё не существует
                        if not Transaction.objects.filter(tx_hash=tx_hash).exists():
                            # Записываем транзакцию консолидации в БД
                            with db_transaction.atomic():
                                Transaction.objects.create(
                                    user=user_wallet.user,
                                    crypto=currency,
                                    amount=amount_to_send,
                                    type="consolidation",
                                    status="pending",
                                    tx_hash=tx_hash,
                                    timestamp=timezone.now(),
                                    fee=Decimal('0'),  # Комиссия уже учтена в расчёте amount_to_send
                                )
                                logger.info(f"[CONSOLIDATION] Transaction saved to DB: {tx_hash}")
                                
                                # Генерируем новый адрес для пользователя сразу после консолидации
                                try:
                                    new_address, private_key = blockchain_service.create_new_address(user_id=user_wallet.user.id)
                                    if new_address:
                                        old_address = user_wallet.deposit_address
                                        user_wallet.deposit_address = new_address
                                        user_wallet.encrypted_private_key = private_key
                                        user_wallet.save()
                                        
                                        # Записываем сгенерированный кошелек в GeneratedWallet
                                        from crypto.models import GeneratedWallet
                                        GeneratedWallet.record_generated_wallet(
                                            address=new_address,
                                            private_key=private_key,
                                            currency=currency,
                                            network=currency.network,
                                            user=user_wallet.user,
                                            wallet_type='user',
                                            created_by='process_pending_deposits_consolidation_parallel',
                                            notes=f'Generated after parallel consolidation for user {user_wallet.user.id}, old address: {old_address}'
                                        )
                                        
                                        logger.info(f"[CONSOLIDATION] Generated new address for user {user_wallet.user.id}: {old_address} -> {new_address}")
                                    else:
                                        logger.warning(f"[CONSOLIDATION] Failed to generate new address for user {user_wallet.user.id}")
                                except Exception as addr_error:
                                    logger.error(f"[CONSOLIDATION] Error generating new address for user {user_wallet.user.id}: {addr_error}")
                                
                                consolidated_count += 1
                        else:
                            logger.warning(f"[CONSOLIDATION] Transaction {tx_hash} already exists in DB")
                    
                    except Exception as e:
                        logger.error(f"[CONSOLIDATION] Error processing consolidation result: {e}")
                        continue
                    
        except Exception as e:
            logger.error(f"Error processing currency {currency.symbol}: {e}")
            continue
    
    logger.info(f"🏁 Consolidation completed: {consolidated_count} transactions processed")
    return f"Consolidation completed: {consolidated_count} transactions"

@shared_task(bind=True, max_retries=20, default_retry_delay=60)
def check_withdrawal_confirmation(self, withdrawal_id: int):
    """
    Проверяет подтверждение транзакции вывода в блокчейне.
    """
    from transactions.models import Withdrawal

    withdrawal = None
    try:
        withdrawal = Withdrawal.objects.select_related('transaction', 'wallet', 'user').get(id=withdrawal_id)
        
        if withdrawal.transaction.status != 'awaiting_confirmation':
            logger.info(f"Withdrawal {withdrawal_id} is not awaiting confirmation. Status: {withdrawal.transaction.status}. Skipping check.")
            return f"skip:not_awaiting_confirmation"

        network = withdrawal.transaction.crypto.network
        tx_hash = withdrawal.transaction.tx_hash

        if not tx_hash:
            logger.error(f"Withdrawal {withdrawal_id} is awaiting confirmation but has no tx_hash. Setting to failed.")
            withdrawal.transaction.status = 'failed'
            withdrawal.transaction.notes = "Transaction hash was missing during confirmation check."
            withdrawal.transaction.save()
            return "error:missing_tx_hash"

        service = get_blockchain_service(network)
        
        try:
            is_confirmed = service.is_transaction_confirmed(tx_hash)
        except Exception as e:
            logger.error(f"Error checking confirmation for withdrawal {withdrawal_id}, tx_hash: {tx_hash}, error: {str(e)}")
            
            # Если это первые несколько попыток - повторяем
            if self.request.retries < 5:
                logger.info(f"Retrying confirmation check for withdrawal {withdrawal_id} (attempt {self.request.retries + 1}/5)")
                raise self.retry(countdown=60, exc=e)
            else:
                # После 5 попыток помечаем как failed
                logger.error(f"Max retries reached for withdrawal {withdrawal_id}, marking as failed")
                withdrawal.transaction.status = 'failed'
                withdrawal.transaction.notes = f"Failed after {self.request.retries + 1} confirmation attempts: {str(e)}"
                withdrawal.transaction.save()
                return f"error:max_retries_reached"

        if is_confirmed:
            logger.info(f"Withdrawal {withdrawal_id} (tx: {tx_hash}) is confirmed on the blockchain.")
            # Сумма для списания = отправленная сумма + комиссия
            amount_to_withdraw = withdrawal.transaction.amount + withdrawal.transaction.fee
            
            with transaction.atomic():
                # Блокируем кошелек для безопасного списания
                user_wallet = UserWallet.objects.select_for_update().get(id=withdrawal.wallet.id)
                
                # Повторная проверка заблокированного баланса на всякий случай
                # При подтверждении проверяем locked_balance, так как средства уже были зарезервированы при отправке
                if user_wallet.locked_balance < amount_to_withdraw:
                    withdrawal.transaction.status = 'failed'
                    withdrawal.transaction.notes = "Insufficient locked funds discovered upon withdrawal confirmation."
                    withdrawal.transaction.save()
                    logger.error(f"Insufficient locked funds for withdrawal {withdrawal.id} upon confirmation. Locked balance: {user_wallet.locked_balance}, required: {amount_to_withdraw}")
                    return "error:insufficient_locked_funds_on_confirmation"

                # Списываем средства
                # Средства уже были списаны с основного баланса,
                # теперь нужно уменьшить заблокированный баланс
                user_wallet.locked_balance -= amount_to_withdraw
                user_wallet.save()

                # Обновляем транзакцию
                withdrawal.transaction.status = 'completed'
                withdrawal.transaction.save()
                
                # Обновляем сам вывод
                withdrawal.confirmation_date = timezone.now()
                withdrawal.save()

            logger.info(f"Successfully finalized withdrawal {withdrawal.id}.")
            return f"success:confirmed_and_completed"
        
        else:
            logger.info(f"Withdrawal {withdrawal_id} (tx: {tx_hash}) is not yet confirmed. Retrying...")
            # Увеличиваем задержку с каждой попыткой
            retry_countdown = 60 * (self.request.retries + 1)
            
            # Проверяем лимит попыток
            if self.request.retries >= self.max_retries:
                logger.error(f"Max retries ({self.max_retries}) reached for withdrawal {withdrawal_id}, marking as failed")
                withdrawal.transaction.status = 'failed'
                withdrawal.transaction.notes = f"Failed to confirm transaction after {self.max_retries} attempts"
                withdrawal.transaction.save()
                return f"error:max_retries_exceeded"
            
            # Делаем retry (это вызовет исключение Retry, которое нормально для Celery)
            # Вызываем retry вне try-except блока
            self.retry(countdown=retry_countdown, max_retries=self.max_retries)

    except Withdrawal.DoesNotExist:
        logger.error(f"Withdrawal with id {withdrawal_id} not found for confirmation check.")
        return f"error:not_found"
    except Retry:
        # Исключение Retry от Celery - просто пропускаем его дальше, это нормально
        raise
    except Exception as e:
        logger.error(f"Error checking confirmation for withdrawal {withdrawal_id}: {e}", exc_info=True)
        
        # Только для реальных ошибок (не Retry) помечаем как failed при превышении лимита
        if self.request.retries >= self.max_retries:
            if withdrawal:
                withdrawal.transaction.status = 'failed'
                withdrawal.transaction.notes = f"Failed to confirm transaction after multiple retries: {str(e)}"
                withdrawal.transaction.save()
                logger.error(f"Withdrawal {withdrawal_id} marked as failed after {self.max_retries} retries")
            return f"error:max_retries_exceeded"
        
        # Пытаемся retry для других ошибок
        retry_countdown = 60 * (self.request.retries + 1)
        logger.info(f"Retrying withdrawal confirmation {withdrawal_id} in {retry_countdown}s (attempt {self.request.retries + 1}/{self.max_retries})")
        self.retry(countdown=retry_countdown, exc=e, max_retries=self.max_retries)


@shared_task
def consolidate_funds():
    """
    Собирает средства с депозитных адресов пользователей на главный системный кошелек.
    """
    logger.info("[CONSOLIDATE] Starting funds consolidation task.")
    
    # Обрабатываем только валюты без MEMO, т.к. только у них есть отдельные адреса
    currencies_to_consolidate = Cryptocurrency.objects.filter(is_active=True, requires_memo=False)
    
    for currency in currencies_to_consolidate:
        logger.info(f"[CONSOLIDATE] Processing currency: {currency.symbol}")
        
        try:
            service = get_blockchain_service(currency.network or currency.symbol)
            system_wallet_address = SystemWalletAddress.objects.get(currency=currency).address
            # Проверяем доступность сервиса через простой запрос баланса
            test_balance = service.get_balance(system_wallet_address)
            logger.debug(f"[CONSOLIDATE] Successfully connected to {currency.symbol} ({currency.network}), system balance: {test_balance}")
        except ValueError as e:
            logger.warning(f"[CONSOLIDATE] Unsupported network {currency.network} for {currency.symbol}. Skipping.")
            continue
        except SystemWalletAddress.DoesNotExist as e:
            logger.error(f"[CONSOLIDATE] No system address for {currency.symbol}. Skipping.")
            continue
        except Exception as e:
            logger.warning(f"[CONSOLIDATE] Service unavailable for {currency.symbol} ({currency.network}): {e}. Skipping.")
            continue

        # Находим все кошельки пользователей с депозитными адресами и балансом
        user_wallets = UserWallet.objects.filter(
            currency=currency,
            is_system_wallet=False,
            deposit_address__isnull=False,
            balance__gt=0  # Обрабатываем только кошельки с балансом
        ).exclude(deposit_address='')

        logger.info(f"[CONSOLIDATE] Found {user_wallets.count()} user wallets with balance for {currency.symbol}")

        for u_wallet in user_wallets:
            try:
                # Получаем актуальный баланс прямо из блокчейна
                try:
                    # Для TRON передаем адрес контракта
                    if hasattr(service, '__class__') and 'Tron' in service.__class__.__name__:
                        contract_address = currency.contract_address if currency.contract_address else None
                        actual_balance = service.get_balance(u_wallet.deposit_address, contract_address)
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

                # Отправляем средства на системный кошелек
                tx_hash = service.send_transaction(
                    private_key=private_key,
                    to_address=system_wallet_address,
                    amount=amount_to_send,
                )
                
                logger.info(f"[CONSOLIDATE] Consolidation transaction sent for user {u_wallet.user.id}. Tx hash: {tx_hash}")

                # Сохраняем транзакцию консолидации в БД
                try:
                    from transactions.models import Transaction
                    # Проверяем что транзакция ещё не существует
                    if not Transaction.objects.filter(tx_hash=tx_hash).exists():
                        Transaction.objects.create(
                            user=u_wallet.user,
                            crypto=currency,
                            amount=amount_to_send,
                            type="consolidation",
                            status="pending",  # Будет обновлено после подтверждения
                            tx_hash=tx_hash,
                            timestamp=timezone.now(),
                            fee=actual_balance - amount_to_send,  # Комиссия газа (разница между балансом и отправленной суммой)
                        )
                        logger.info(f"[CONSOLIDATE] Consolidation transaction saved to DB: {tx_hash}")
                    else:
                        logger.warning(f"[CONSOLIDATE] Transaction {tx_hash} already exists in DB")
                except Exception as db_error:
                    logger.error(f"[CONSOLIDATE] Failed to save consolidation transaction to DB: {db_error}")

                # НЕ обнуляем баланс сразу - это делается после подтверждения транзакции в блокчейне

            except Exception as e:
                logger.error(f"[CONSOLIDATE] Failed to consolidate for user {u_wallet.user.id}, currency {currency.symbol}. Error: {e}", exc_info=True)

    logger.info("[CONSOLIDATE] Finished funds consolidation task.")

