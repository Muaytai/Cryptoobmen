
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
                    
                    # Проверяем, является ли это RPC ошибкой
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
                        # Если это не RPC ошибка или исчерпаны попытки
                        break
            
            # Если все попытки исчерпаны
            logger.error(f"\033[91mFailed after {max_retries + 1} attempts. Last error: {last_exception}\033[0m")
            raise last_exception
            
        return wrapper
    return decorator


def get_min_consolidation_amount(currency: Cryptocurrency) -> Decimal:
    """Минимальная сумма для консолидации в зависимости от валюты"""
    minimums = {
        'POL': Decimal('0.01'),    # Снижено - теперь используем динамический расчёт газа
        'BTC': Decimal('0.0001'),
        'ETH': Decimal('0.01'),
        'TRX': Decimal('10'),
        'USDT': Decimal('10'),     # Добавлено для USDT TRC-20
    }
    return minimums.get(currency.symbol, Decimal('0.001'))

def get_gas_reserve(currency: Cryptocurrency) -> Decimal:
    """Резерв для покрытия комиссии газа в зависимости от валюты"""
    reserves = {
        'POL': Decimal('0.01'),    # Снижено после введения динамического расчёта
        'BTC': Decimal('0.00005'), 
        'ETH': Decimal('0.005'),
        'TRX': Decimal('1'),
        # USDT (TRC20) - газ платится в TRX, не в USDT!
        'USDT': Decimal('0'),  # Для USDT газ не нужен
    }
    return reserves.get(currency.symbol, Decimal('0.001'))

def get_system_wallet_address(currency: Cryptocurrency) -> str:
    """Получает адрес системного кошелька для заданной валюты"""
    try:
        # Сначала пробуем найти в SystemWalletAddress
        from .models import SystemWalletAddress
        system_wallet_address = SystemWalletAddress.objects.get(currency=currency)
        
        # Записываем сгенерированный кошелек в GeneratedWallet если его там нет
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
            # Запись уже существует, это нормально
            pass
        
        return system_wallet_address.address
        
    except SystemWalletAddress.DoesNotExist:
        # Fallback - ищем в UserWallet (старый способ)
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
    Проверяет подтверждения транзакций консолидации в блокчейне.
    """
    start_time = timezone.now()
    logger.info("\033[94m" + "="*60 + "\033[0m")
    logger.info("\033[94m🔍 [CONFIRMATION] Starting consolidation confirmations check...\033[0m")
    logger.info(f"\033[94m⏰ Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\033[0m")
    
    # Находим все ожидающие подтверждения консолидации
    pending_consolidations = Transaction.objects.filter(
        type="consolidation",
        status="pending"
    )
    
    logger.info(f"\033[94m📋 Found {pending_consolidations.count()} pending consolidation transactions\033[0m")
    confirmed = 0
    
    for tx in pending_consolidations:
        try:
            logger.info(f"\033[94m🔍 Checking confirmation for tx: {tx.tx_hash[:16]}... ({tx.crypto.symbol})\033[0m")
            service = get_blockchain_service(tx.crypto.network or tx.crypto.symbol)
            
            # Проверяем подтверждение транзакции с retry логикой
            @retry_on_rpc_error(max_retries=2, delay=1, backoff=1.5)
            def check_transaction_confirmation():
                return service.is_transaction_confirmed(tx.tx_hash)
            
            is_confirmed = check_transaction_confirmation()
            logger.info(f"\033[94m📊 Transaction {tx.tx_hash[:16]}... confirmed: {is_confirmed}\033[0m")
            
            if is_confirmed:
                with transaction.atomic():
                    # Обновляем статус транзакции консолидации
                    tx.status = "completed"
                    tx.save()
                    
                    # Получаем кошелек пользователя
                    user_wallet = UserWallet.objects.get(
                        user=tx.user,
                        currency=tx.crypto,
                        is_system_wallet=False
                    )
                    
                    # Находим все депозиты в статусе pending для этого пользователя и валюты
                    pending_deposits = Transaction.objects.filter(
                        user=tx.user,
                        crypto=tx.crypto,
                        type="deposit",
                        status="pending"
                    )
                    
                    # Зачисляем средства на баланс из всех pending депозитов
                    total_credited = Decimal('0')
                    for deposit in pending_deposits:
                        # Обновляем статус депозита
                        deposit.status = "completed"
                        deposit.save()
                        
                        # Зачисляем на баланс (минус gas который уже учтен в fee)
                        net_amount = deposit.amount - deposit.fee
                        user_wallet.balance += net_amount
                        total_credited += net_amount
                        
                        logger.info(f"\033[94mCredited deposit {deposit.tx_hash}: gross={deposit.amount}, gas={deposit.fee}, net={net_amount} {tx.crypto.symbol}\033[0m")
                    
                    if total_credited > 0:
                        user_wallet.save()
                        logger.info(f"\033[92m✅ Consolidation completed for user {tx.user.id}: credited {total_credited} {tx.crypto.symbol} from {pending_deposits.count()} deposits\033[0m")
                    else:
                        logger.warning(f"\033[93m⚠️ Consolidation {tx.tx_hash} completed but no pending deposits found to credit\033[0m")
                    
                    confirmed += 1
                    
                    # Генерируем новый адрес для пользователя после успешной консолидации
                    try:
                        logger.info(f"\033[94m🔄 Generating new deposit address for user {tx.user.id} after consolidation\033[0m")
                        
                        # Получаем старый адрес
                        old_address = user_wallet.deposit_address
                        
                        # Генерируем новый адрес
                        blockchain_service = get_blockchain_service(tx.crypto.network or tx.crypto.symbol)
                        new_address, private_key = blockchain_service.create_new_address()
                        
                        # Обновляем адрес в кошельке пользователя
                        user_wallet.deposit_address = new_address
                        user_wallet.encrypted_private_key = private_key
                        user_wallet.save()
                        
                        # Записываем в GeneratedWallet
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
                        
                        logger.info(f"\033[92m✅ Generated new address for user {tx.user.id}: {old_address} -> {new_address}\033[0m")
                        
                    except Exception as addr_error:
                        logger.error(f"\033[91m❌ Error generating new address for user {tx.user.id}: {addr_error}\033[0m")
                    
        except Exception as e:
            logger.error(f"\033[91m❌ Error checking consolidation confirmation for {tx.tx_hash}: {e}\033[0m")
            continue
    
    end_time = timezone.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info(f"\033[94m" + "="*60 + "\033[0m")
    logger.info(f"\033[94m🏁 [CONFIRMATION] Process completed\033[0m")
    logger.info(f"\033[94m✅ Confirmed transactions: {confirmed}\033[0m")
    logger.info(f"\033[94m⏱️ Duration: {duration:.2f} seconds\033[0m")
    logger.info(f"\033[94m⏰ End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\033[0m")
    logger.info(f"\033[94m" + "="*60 + "\033[0m")
    
    return f"Checked consolidation confirmations: {confirmed} confirmed"


@shared_task
def consolidate_user_deposits():
    """
    Консолидация депозитов - перевод средств с пользовательских адресов на системный кошелек.
    Работает только для валют без MEMO (POL, BTC, ETH).
    """
    processed = 0
    start_time = timezone.now()
    logger.info("\033[94m" + "="*60 + "\033[0m")
    logger.info("\033[94m🚀 [CONSOLIDATION] Starting consolidation process...\033[0m")
    logger.info(f"\033[94m⏰ Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\033[0m")
    
    # Получаем все активные валюты без MEMO
    currencies_no_memo = Cryptocurrency.objects.filter(
        is_active=True, 
        requires_memo=False
    )
    
    logger.info(f"\033[94m📊 Found {currencies_no_memo.count()} currencies without MEMO: {[c.symbol for c in currencies_no_memo]}\033[0m")
    
    for currency in currencies_no_memo:
        logger.info(f"\033[94m" + "-"*50 + "\033[0m")
        logger.info(f"\033[94m🔄 Processing consolidation for {currency.symbol} ({currency.network})\033[0m")
        
        try:
            # Получаем системный кошелек
            system_wallet = UserWallet.objects.get(
                user=None,
                currency=currency,
                is_system_wallet=True,
                is_active=True
            )
            
            if not system_wallet.encrypted_private_key:
                logger.warning(f"\033[93mSystem wallet for {currency.symbol} has no private key, skipping\033[0m")
                continue
                
            # Получаем все пользовательские кошельки с балансом на блокчейне
            user_wallets = UserWallet.objects.filter(
                currency=currency,
                is_system_wallet=False,
                deposit_address__isnull=False,
                encrypted_private_key__isnull=False  # Только кошельки с приватными ключами
            ).exclude(deposit_address='')
            
            logger.info(f"\033[94m👥 Found {user_wallets.count()} user wallets for {currency.symbol}\033[0m")
            
            blockchain_service = get_blockchain_service(currency.network or currency.symbol)
            logger.info(f"\033[94m🔗 Connected to {currency.network} blockchain service\033[0m")
            
            currency_processed = 0
            for user_wallet in user_wallets:
                try:
                    logger.info(f"\033[94m👤 Processing user {user_wallet.user.id} wallet: {user_wallet.deposit_address[:10]}...\033[0m")
                    
                    # Проверяем баланс на блокчейне
                    blockchain_balance = blockchain_service.get_balance(user_wallet.deposit_address)
                    logger.info(f"\033[94m💰 Blockchain balance: {blockchain_balance} {currency.symbol}\033[0m")
                    
                    # Минимальная сумма для консолидации (чтобы покрыть комиссию)
                    min_consolidation_amount = get_min_consolidation_amount(currency)
                    logger.info(f"\033[94m📏 Minimum threshold: {min_consolidation_amount} {currency.symbol}\033[0m")
                    
                    if blockchain_balance < min_consolidation_amount:
                        logger.info(f"\033[93m⚠️ Balance {blockchain_balance} {currency.symbol} too small for consolidation (min: {min_consolidation_amount})\033[0m")
                        continue
                    
                    # Рассчитываем сумму к переводу (оставляем немного на комиссию)
                    gas_reserve = get_gas_reserve(currency)
                    amount_to_send = blockchain_balance - gas_reserve
                    logger.info(f"\033[94m⛽ Gas reserve: {gas_reserve} {currency.symbol}\033[0m")
                    logger.info(f"\033[94m💸 Amount to send: {amount_to_send} {currency.symbol}\033[0m")
                    
                    if amount_to_send <= 0:
                        logger.warning(f"\033[93m⚠️ Amount to send {amount_to_send} {currency.symbol} is zero or negative after gas reserve\033[0m")
                        continue
                    
                    logger.info(f"\033[94m🚀 Consolidating {amount_to_send} {currency.symbol} from {user_wallet.deposit_address} to system wallet\033[0m")
                    
                    # Выполняем перевод с retry логикой
                    @retry_on_rpc_error(max_retries=3, delay=2, backoff=2)
                    def send_consolidation_transaction():
                        return blockchain_service.send_transaction(
                            private_key=user_wallet.encrypted_private_key,
                            to_address=get_system_wallet_address(currency),
                            amount=amount_to_send,
                            memo=f"consolidation_{user_wallet.user_id}"
                        )
                    
                    tx_hash = send_consolidation_transaction()
                    logger.info(f"\033[92m✅ Transaction sent successfully: {tx_hash}\033[0m")
                    
                    # Записываем транзакцию консолидации
                    with transaction.atomic():
                        Transaction.objects.create(
                            user=user_wallet.user,
                            crypto=currency,
                            amount=amount_to_send,
                            tx_hash=tx_hash,
                            type="consolidation",
                            status="pending",
                            timestamp=timezone.now()
                        )
                    
                    processed += 1
                    currency_processed += 1
                    logger.info(f"\033[92m💾 Consolidation transaction saved to DB: {tx_hash}\033[0m")
                    logger.info(f"\033[92m🎉 Successfully consolidated {amount_to_send} {currency.symbol} for user {user_wallet.user.id}\033[0m")
                    
                except Exception as e:
                    logger.error(f"\033[91m❌ Error consolidating {currency.symbol} for user {user_wallet.user_id}: {e}\033[0m")
                    continue
            
            logger.info(f"\033[94m📈 Currency {currency.symbol} summary: {currency_processed} transactions processed\033[0m")
                    
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

