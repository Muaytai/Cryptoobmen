"""
Задачи консолидации средств - вспомогательные функции и проверка подтверждений
"""
from __future__ import annotations

import logging
import time
from decimal import Decimal
from datetime import timedelta
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
        'ETH': Decimal('0.0001'),
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
    ⚠️ КРИТИЧЕСКИ ВАЖНАЯ ФУНКЦИЯ: Проверяет подтверждения транзакций консолидации в блокчейне.
    
    ВАЖНО ДЛЯ АГЕНТОВ:
    После подтверждения консолидации нужно зачислить пользователю tx.amount (сумму из транзакции консолидации),
    а НЕ сумму депозита или deposit.amount - deposit.fee. 
    
    tx.amount содержит реальную сумму, которая была отправлена (максимально возможную).
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
                    
                    # Сохраняем старый адрес для WebSocket уведомления (до генерации нового)
                    old_deposit_address = user_wallet.deposit_address
                    
                    # ⚠️ КРИТИЧЕСКИ ВАЖНАЯ ЛОГИКА ЗАЧИСЛЕНИЯ ПОСЛЕ КОНСОЛИДАЦИИ:
                    # Зачисляем пользователю РЕАЛЬНУЮ сумму, которая была консолидирована (tx.amount)
                    # Это amount_to_send из consolidate_user_deposits - вся сумма с блокчейна минус газ
                    # НЕ используем deposit.amount - deposit.fee, т.к. это неправильно для больших депозитов!
                    consolidation_amount = tx.amount  # Реальная консолидированная сумма (максимально возможная)
                    logger.info(f"\033[94m💰 Consolidation amount (will be credited to user): {consolidation_amount} {tx.crypto.symbol}\033[0m")
                    
                    # Находим все депозиты в статусе pending для этого пользователя и валюты
                    pending_deposits = Transaction.objects.filter(
                        user=tx.user,
                        crypto=tx.crypto,
                        type="deposit",
                        status="pending"
                    )
                    
                    logger.info(f"\033[94m📋 Found {pending_deposits.count()} pending deposits for user {tx.user.id}\033[0m")
                    
                    # Зачисляем пользователю РЕАЛЬНУЮ консолидированную сумму
                    # ⚠️ ВАЖНО: Зачисляем сумму из транзакции консолидации (tx.amount), а не сумму депозита!
                    # ⚠️ КРИТИЧЕСКИ ВАЖНО: Увеличиваем и balance, и available_balance!
                    user_wallet.balance += consolidation_amount
                    user_wallet.available_balance += consolidation_amount  # ⚠️ ВАЖНО: Увеличиваем available_balance тоже!
                    total_pending_deposits_value = sum(dep.amount for dep in pending_deposits)
                    
                    # Обновляем статусы всех pending депозитов на completed
                    for deposit in pending_deposits:
                        deposit.status = "completed"
                        deposit.save()
                        logger.info(f"\033[94m✅ Marked deposit {deposit.tx_hash} as completed (was pending)\033[0m")
                    
                    if consolidation_amount > 0:
                        user_wallet.save(update_fields=['balance', 'available_balance'])  # Явно указываем поля для сохранения
                        logger.info(f"\033[92m✅ Consolidation completed for user {tx.user.id}: credited {consolidation_amount} {tx.crypto.symbol}\033[0m")
                        logger.info(f"\033[94m📊 Balance: {user_wallet.balance} {tx.crypto.symbol}, Available: {user_wallet.available_balance} {tx.crypto.symbol}\033[0m")
                        logger.info(f"\033[94m📊 Total pending deposits value was: {total_pending_deposits_value} {tx.crypto.symbol}\033[0m")
                        logger.info(f"\033[94m💡 Note: User credited with consolidated amount ({consolidation_amount}), not deposit amount ({total_pending_deposits_value})\033[0m")
                        
                        # Отправляем WebSocket уведомление о зачислении средств на СТАРЫЙ адрес
                        # (до генерации нового адреса, т.к. фронтенд подключен к старому адресу)
                        try:
                            from channels.layers import get_channel_layer
                            from asgiref.sync import async_to_sync
                            
                            channel_layer = get_channel_layer()
                            if channel_layer and old_deposit_address:
                                logger.info(f"\033[94m📡 Sending WebSocket notification for address {old_deposit_address}\033[0m")
                                async_to_sync(channel_layer.group_send)(
                                    f"deposit_address_{old_deposit_address}",
                                    {
                                        "type": "deposit_status_update",
                                        "data": {
                                            'address': old_deposit_address,
                                            'status': 'used',
                                            'message': 'Deposit completed',
                                            'amount': str(consolidation_amount),
                                            'currency': tx.crypto.symbol
                                        }
                                    }
                                )
                                logger.info(f"\033[92m✅ WebSocket notification sent to {old_deposit_address}\033[0m")
                        except Exception as ws_error:
                            logger.error(f"\033[91m❌ Failed to send WebSocket notification: {ws_error}\033[0m")
                    else:
                        logger.warning(f"\033[93m⚠️ Consolidation {tx.tx_hash} completed but consolidation amount is zero\033[0m")
                    
                    confirmed += 1
                    
                    # ⚠️ ВАЖНО: Генерируем новый адрес для пользователя после успешной консолидации
                    # Это критично, т.к. старый адрес был опустошен и более не используется
                    # История: 
                    # - 2343a8ec (Dmitry Shishkov): добавлена генерация адреса после консолидации
                    # - 91b3b270 (Makc): отключена с комментарием "работает без консолидации"
                    # - Восстановлено т.к. консолидация снова активна
                    try:
                        logger.info(f"\033[94m🔄 Generating new deposit address for user {tx.user.id} after consolidation\033[0m")
                        
                        # Получаем старый адрес
                        old_address = user_wallet.deposit_address
                        
                        if not old_address:
                            logger.warning(f"\033[93m⚠️ User {tx.user.id} has no deposit address to replace, skipping address generation\033[0m")
                        else:
                            # Генерируем новый адрес
                            blockchain_service = get_blockchain_service(tx.crypto.network or tx.crypto.symbol)
                            new_address, private_key = blockchain_service.create_new_address()
                            
                            if not new_address or not private_key:
                                raise ValueError(f"Blockchain service returned empty address or key: address={new_address}, key={'***' if private_key else 'None'}")
                            
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
                            
                            logger.info(f"\033[92m✅ Generated new address for user {tx.user.id}: {old_address[:10]}... -> {new_address[:10]}...\033[0m")
                        
                    except Exception as addr_error:
                        import traceback
                        error_trace = traceback.format_exc()
                        logger.error(f"\033[91m❌ Error generating new address for user {tx.user.id}: {addr_error}\033[0m")
                        logger.error(f"\033[91m❌ Traceback: {error_trace}\033[0m")
                        # НЕ прерываем выполнение - адрес можно сгенерировать позже через API
                    
        except Exception as e:
            logger.error(f"\033[91m❌ Error checking consolidation confirmation for {tx.tx_hash}: {e}\033[0m")
            continue
    
    # Дополнительная проверка: обновляем pending депозиты, для которых уже есть подтвержденная консолидация
    # Это нужно для случаев, когда депозит был обнаружен после того, как консолидация уже подтвердилась
    logger.info(f"\033[94m🔍 Checking for pending deposits with already confirmed consolidations...\033[0m")
    from crypto.models import Cryptocurrency
    currencies_no_memo = Cryptocurrency.objects.filter(is_active=True, requires_memo=False)
    logger.info(f"\033[94m📊 Found {currencies_no_memo.count()} currencies without MEMO\033[0m")
    
    for currency in currencies_no_memo:
        # Находим все подтвержденные консолидации для этой валюты
        confirmed_consolidations = Transaction.objects.filter(
            type="consolidation",
            status="completed",
            crypto=currency
        ).select_related('user')
        
        logger.info(f"\033[94m📋 Found {confirmed_consolidations.count()} confirmed consolidations for {currency.symbol}\033[0m")
        
        for consolidation in confirmed_consolidations:
            # Находим pending депозиты для этого пользователя и валюты
            pending_deposits = Transaction.objects.filter(
                user=consolidation.user,
                crypto=currency,
                type="deposit",
                status="pending"
            )
            
            logger.info(f"\033[94m👤 User {consolidation.user.id} ({consolidation.user.email}): {pending_deposits.count()} pending deposits\033[0m")
            
            if pending_deposits.exists():
                # Проверяем баланс на адресе - если 0, значит средства уже консолидированы
                try:
                    user_wallet = UserWallet.objects.get(
                        user=consolidation.user,
                        currency=currency,
                        is_system_wallet=False
                    )
                    if user_wallet.deposit_address:
                        service = get_blockchain_service(currency.network or currency.symbol)
                        blockchain_balance = service.get_balance(user_wallet.deposit_address)
                        logger.info(f"\033[94m💰 User {consolidation.user.id} address {user_wallet.deposit_address}: balance = {blockchain_balance} {currency.symbol}\033[0m")
                        
                        # Если баланс 0 и есть подтвержденная консолидация, обновляем депозиты
                        # Зачисление уже произошло при подтверждении консолидации, просто обновляем статус
                        if blockchain_balance == 0:
                            logger.info(f"\033[94m✅ Found {pending_deposits.count()} pending deposits for user {consolidation.user.id} with confirmed consolidation and zero balance\033[0m")
                            
                            # Обновляем статусы депозитов на completed
                            # Зачисление уже произошло при подтверждении консолидации
                            for deposit in pending_deposits:
                                deposit.status = "completed"
                                deposit.save()
                                logger.info(f"\033[94m✅ Marked deposit {deposit.tx_hash or deposit.transaction_id} as completed (consolidation already confirmed)\033[0m")
                except UserWallet.DoesNotExist:
                    continue
                except Exception as e:
                    logger.error(f"\033[91m❌ Error checking balance for user {consolidation.user.id}: {e}\033[0m")
                    continue
    
    # Дополнительная проверка: ищем pending депозиты без консолидаций
    # Это может быть случай, когда депозит обнаружен, но консолидация еще не создана или не подтвердилась
    logger.info(f"\033[94m🔍 Checking for pending deposits without consolidations...\033[0m")
    for currency in currencies_no_memo:
        # Находим все pending депозиты для этой валюты
        all_pending_deposits = Transaction.objects.filter(
            crypto=currency,
            type="deposit",
            status="pending"
        ).select_related('user')
        
        if all_pending_deposits.exists():
            logger.info(f"\033[94m📋 Found {all_pending_deposits.count()} total pending deposits for {currency.symbol}\033[0m")
            
            for deposit in all_pending_deposits:
                # Проверяем, есть ли консолидация (pending или completed) для этого пользователя
                has_consolidation = Transaction.objects.filter(
                    user=deposit.user,
                    crypto=currency,
                    type="consolidation"
                ).exists()
                
                if not has_consolidation:
                    logger.info(f"\033[94m⚠️ User {deposit.user.id} has pending deposit {deposit.tx_hash or deposit.transaction_id} but no consolidation transaction\033[0m")
                    
                    # Проверяем баланс на адресе - если 0, значит средства уже консолидированы
                    try:
                        user_wallet = UserWallet.objects.get(
                            user=deposit.user,
                            currency=currency,
                            is_system_wallet=False
                        )
                        if user_wallet.deposit_address:
                            service = get_blockchain_service(currency.network or currency.symbol)
                            blockchain_balance = service.get_balance(user_wallet.deposit_address)
                            logger.info(f"\033[94m💰 User {deposit.user.id} address {user_wallet.deposit_address}: balance = {blockchain_balance} {currency.symbol}\033[0m")
                            
                            # Если баланс 0, значит средства уже консолидированы (возможно, вручную или другой транзакцией)
                            # Обновляем статус депозита и зачисляем средства пользователю
                            if blockchain_balance == 0:
                                logger.info(f"\033[94m✅ User {deposit.user.id} has zero balance, marking deposit as completed\033[0m")
                                
                                # Зачисляем сумму депозита пользователю
                                deposit_amount = deposit.amount
                                user_wallet.balance += deposit_amount
                                user_wallet.available_balance += deposit_amount
                                user_wallet.save()
                                
                                # Обновляем статус депозита
                                deposit.status = "completed"
                                deposit.save()
                                logger.info(f"\033[94m✅ Marked deposit {deposit.tx_hash or deposit.transaction_id} as completed and credited {deposit_amount} {currency.symbol} to user {deposit.user.id}\033[0m")
                    except UserWallet.DoesNotExist:
                        logger.warning(f"\033[91m⚠️ UserWallet not found for user {deposit.user.id}, currency {currency.symbol}\033[0m")
                        continue
                    except Exception as e:
                        logger.error(f"\033[91m❌ Error checking balance for user {deposit.user.id}: {e}\033[0m")
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
    ⚠️ КРИТИЧЕСКИ ВАЖНАЯ ЛОГИКА КОНСОЛИДАЦИИ:
    
    Консолидация депозитов - перевод средств с пользовательских адресов на системный кошелек.
    Работает только для валют без MEMO (POL, BTC, ETH).
    
    ВАЖНО ДЛЯ АГЕНТОВ:
    1. Баланс пользователя НЕ увеличивается при обнаружении депозита - он остается в статусе "pending"
    2. Консолидация работает с РЕАЛЬНЫМ балансом блокчейна (get_balance), а НЕ с балансом в БД
    3. Консолидируется МАКСИМАЛЬНО ВОЗМОЖНАЯ сумма: blockchain_balance - gas_reserve
    4. Эта сумма (amount_to_send) записывается в транзакцию консолидации (tx.amount)
    5. После подтверждения консолидации пользователю зачисляется tx.amount (РЕАЛЬНАЯ консолидированная сумма)
    6. НИКОГДА не используйте deposit.amount - deposit.fee - это неправильно!
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
            # Включаем кошельки с encrypted_private_key или с ключом в GeneratedWallet
            user_wallets = UserWallet.objects.filter(
                currency=currency,
                is_system_wallet=False,
                deposit_address__isnull=False
            ).exclude(deposit_address='')
            
            logger.info(f"\033[94m👥 Found {user_wallets.count()} user wallets for {currency.symbol}\033[0m")
            
            blockchain_service = get_blockchain_service(currency.network or currency.symbol)
            logger.info(f"\033[94m🔗 Connected to {currency.network} blockchain service\033[0m")
            
            currency_processed = 0
            for user_wallet in user_wallets:
                try:
                    logger.info(f"\033[94m👤 Processing user {user_wallet.user.id} wallet: {user_wallet.deposit_address[:10]}...\033[0m")
                    
                    # Проверяем наличие приватного ключа (либо в encrypted_private_key, либо в GeneratedWallet)
                    private_key_input = user_wallet.encrypted_private_key or ""
                    if not private_key_input:
                        from .models import GeneratedWallet
                        gw = GeneratedWallet.objects.filter(address=user_wallet.deposit_address).first()
                        if gw and gw.private_key:
                            private_key_input = gw.private_key
                            logger.info(f"\033[94m🔑 Found private key in GeneratedWallet for {user_wallet.deposit_address[:10]}...\033[0m")
                        else:
                            logger.warning(f"\033[93m⚠️ No private key found for wallet {user_wallet.deposit_address[:10]}... (neither in encrypted_private_key nor in GeneratedWallet), skipping\033[0m")
                            continue
                    
                    # ⚠️ КРИТИЧЕСКИ ВАЖНО: Кошелек одноразовый, нужно ОПУСТОШИТЬ его максимально!
                    # Используем точный расчет максимальной суммы через get_max_sendable_amount или аналогичный метод
                    # НЕ используем gas_reserve - это приводит к неполной консолидации!
                    
                    # Для TRC-20 токенов передаем contract_address при получении баланса
                    contract_address = currency.contract_address if currency.network and currency.network.upper() == 'TRC20' else None
                    if contract_address:
                        blockchain_balance = blockchain_service.get_balance(user_wallet.deposit_address, contract_address=contract_address)
                    else:
                        blockchain_balance = blockchain_service.get_balance(user_wallet.deposit_address)
                    logger.info(f"\033[94m💰 Blockchain balance: {blockchain_balance} {currency.symbol}\033[0m")
                    
                    # Минимальная сумма для консолидации (чтобы покрыть комиссию)
                    min_consolidation_amount = get_min_consolidation_amount(currency)
                    logger.info(f"\033[94m📏 Minimum threshold: {min_consolidation_amount} {currency.symbol}\033[0m")
                    
                    if blockchain_balance < min_consolidation_amount:
                        logger.info(f"\033[93m⚠️ Balance {blockchain_balance} {currency.symbol} too small for consolidation (min: {min_consolidation_amount})\033[0m")
                        continue
                    
                    # ⚠️ ИЗЯЩНОЕ РЕШЕНИЕ RACE CONDITION:
                    # Проверяем наличие pending депозитов. Если их нет, но есть баланс - проверяем транзакции в блокчейне.
                    # Это позволяет:
                    # 1. Предотвратить консолидацию до записи депозита (race condition)
                    # 2. Но все равно консолидировать пропущенные сканированием депозиты
                    pending_deposits = Transaction.objects.filter(
                        user=user_wallet.user,
                        crypto=currency,
                        type="deposit",
                        status="pending"
                    )
                    
                    # Дополнительная проверка: если есть совсем свежие депозиты (менее 5 секунд), ждем немного
                    # Это защита от race condition, когда депозит только что создан
                    if pending_deposits.count() == 0:
                        very_recent_deposits = Transaction.objects.filter(
                            user=user_wallet.user,
                            crypto=currency,
                            type="deposit",
                            timestamp__gte=timezone.now() - timedelta(seconds=5)
                        ).exists()
                        
                        if very_recent_deposits:
                            logger.info(f"\033[94m⏳ Very recent deposit found (<5s), waiting 3 seconds to ensure DB commit...\033[0m")
                            time.sleep(3)
                            
                            # Проверяем еще раз после задержки
                            pending_deposits = Transaction.objects.filter(
                                user=user_wallet.user,
                                crypto=currency,
                                type="deposit",
                                status="pending"
                            )
                    
                    if pending_deposits.count() == 0:
                        # Нет pending депозитов - проверяем, есть ли свежие транзакции в блокчейне
                        # Это может быть пропущенный сканированием депозит
                        logger.info(f"\033[94m🔍 No pending deposits for user {user_wallet.user.id}, checking blockchain for recent transactions...\033[0m")
                        
                        try:
                            # Проверяем транзакции за последние 10 минут
                            recent_window = int((timezone.now() - timedelta(minutes=10)).timestamp() * 1000)
                            
                            # Получаем транзакции из блокчейна (используем тот же contract_address что выше)
                            if contract_address:
                                recent_txs = blockchain_service.get_transactions(
                                    address=user_wallet.deposit_address,
                                    min_timestamp=recent_window,
                                    contract_address=contract_address
                                )
                            else:
                                recent_txs = blockchain_service.get_transactions(
                                    address=user_wallet.deposit_address,
                                    min_timestamp=recent_window
                                )
                            
                            # Проверяем, есть ли транзакции, которых нет в БД
                            if recent_txs:
                                logger.info(f"\033[94m📥 Found {len(recent_txs)} recent blockchain transactions, checking if they're in DB...\033[0m")
                                
                                found_missed = False
                                for tx_data in recent_txs:
                                    tx_hash_from_blockchain = tx_data.get('transaction_id')
                                    
                                    # Проверяем, есть ли эта транзакция в БД
                                    existing_tx = Transaction.objects.filter(
                                        tx_hash=tx_hash_from_blockchain,
                                        user=user_wallet.user,
                                        crypto=currency
                                    ).first()
                                    
                                    if not existing_tx:
                                        logger.warning(f"\033[93m⚠️ Found missed deposit transaction {tx_hash_from_blockchain} on blockchain! This should be processed by deposit scanner.\033[0m")
                                        found_missed = True
                                        break
                                
                                if not found_missed:
                                    # Все транзакции найдены в БД, но нет pending - возможно они уже обработаны
                                    # Это может быть race condition или транзакции уже были консолидированы
                                    logger.info(f"\033[94m✅ All recent transactions are in DB. Checking if this is a race condition...\033[0m")
                                    
                                    # Проверяем, есть ли совсем свежие депозиты (менее 30 секунд назад)
                                    very_recent = Transaction.objects.filter(
                                        user=user_wallet.user,
                                        crypto=currency,
                                        type="deposit",
                                        timestamp__gte=timezone.now() - timedelta(seconds=30)
                                    ).exists()
                                    
                                    if very_recent:
                                        logger.info(f"\033[94m⏳ Very recent deposit found (<30s), waiting 2 seconds to avoid race condition...\033[0m")
                                        time.sleep(2)
                                        
                                        # Проверяем еще раз после небольшой задержки
                                        pending_after_delay = Transaction.objects.filter(
                                            user=user_wallet.user,
                                            crypto=currency,
                                            type="deposit",
                                            status="pending"
                                        ).exists()
                                        
                                        if not pending_after_delay:
                                            logger.info(f"\033[93m⏭️  Still no pending deposits after delay, skipping to avoid race condition\033[0m")
                                            continue
                                    else:
                                        # Нет совсем свежих депозитов, но есть баланс - это может быть пропущенный депозит
                                        # Консолидируем, чтобы средства не оставались на адресе
                                        logger.info(f"\033[94m💡 No very recent deposits, but balance exists. Consolidating to prevent stuck funds.\033[0m")
                            else:
                                # Нет свежих транзакций в блокчейне - это старый баланс, возможно от предыдущей консолидации
                                logger.info(f"\033[93m⏭️  No recent blockchain transactions and no pending deposits. Skipping consolidation.\033[0m")
                                continue
                                
                        except Exception as check_error:
                            # При ошибке проверки транзакций продолжаем консолидацию
                            logger.warning(f"\033[93m⚠️ Error checking blockchain transactions: {check_error}. Proceeding with consolidation.\033[0m")
                    else:
                        logger.info(f"\033[94m✅ Found {pending_deposits.count()} pending deposits, proceeding with consolidation\033[0m")
                    
                    # Рассчитываем МАКСИМАЛЬНУЮ сумму к переводу (всё что можно отправить)
                    # ⚠️ ВАЖНО: Используем точный расчет через методы блокчейн-сервиса, НЕ gas_reserve!
                    system_wallet_address = get_system_wallet_address(currency)
                    gas_cost = Decimal('0')  # Инициализируем gas_cost
                    
                    # ⚠️ ВАЖНО: Используем точные методы расчета максимальной суммы для каждой валюты
                    # Для Polygon и Ethereum (нативная валюта) используем get_max_sendable_amount
                    # Это гарантирует точный расчет с учетом того, что газ вычитается из баланса
                    if hasattr(blockchain_service, 'get_max_sendable_amount'):
                        amount_to_send = blockchain_service.get_max_sendable_amount(
                            user_wallet.deposit_address,
                            system_wallet_address
                        )
                        # Рассчитываем реальную стоимость газа: баланс - отправляемая сумма
                        gas_cost = blockchain_balance - amount_to_send
                        logger.info(f"\033[94m💸 Max sendable amount (calculated via get_max_sendable_amount): {amount_to_send} {currency.symbol}\033[0m")

                        logger.info(f"\033[94m⛽ Gas cost (calculated): {gas_cost} {currency.symbol}\033[0m")
                    # Для Ethereum используем estimate_gas_fee для точного расчета
                    elif hasattr(blockchain_service, 'estimate_gas_fee'):
                        gas_info = blockchain_service.estimate_gas_fee(
                            to_address=system_wallet_address,
                            amount=blockchain_balance,
                            contract_address=getattr(currency, 'contract_address', None)
                        )
                        # estimate_gas_fee возвращает словарь с 'gas_fee_eth' или 'gas_fee_eth'
                        gas_cost = gas_info.get('gas_fee_eth', Decimal('0'))
                        amount_to_send = blockchain_balance - gas_cost
                        logger.info(f"\033[94m⛽ Gas cost (from estimate_gas_fee): {gas_cost} {currency.symbol}\033[0m")
                        logger.info(f"\033[94m💸 Amount to send (balance - gas): {amount_to_send} {currency.symbol}\033[0m")

                    # Для Bitcoin можно отправить amount=0 для sweep всех средств
                    elif currency.symbol == 'BTC':
                        amount_to_send = Decimal('0')  # 0 означает "отправить всё" (sweep)
                        # Для Bitcoin газ рассчитывается автоматически при sweep, но мы можем оценить его
                        # Используем фиксированный резерв для оценки
                        gas_cost = get_gas_reserve(currency)
                        logger.info(f"\033[94m💸 Bitcoin sweep mode: will send all funds\033[0m")
                        logger.info(f"\033[94m⛽ Estimated gas cost for BTC: {gas_cost} {currency.symbol}\033[0m")
                    else:
                        # Fallback: для других валют оцениваем газ динамически через gas_calculation
                        from .gas_calculation import calculate_estimated_gas_cost
                        gas_cost = calculate_estimated_gas_cost(
                            currency=currency,
                            deposit_amount=blockchain_balance,
                            user_address=user_wallet.deposit_address
                        )
                        amount_to_send = blockchain_balance - gas_cost
                        logger.info(f"\033[94m⛽ Gas cost (estimated via gas_calculation): {gas_cost} {currency.symbol}\033[0m")
                        logger.info(f"\033[94m💸 Amount to send (balance - gas): {amount_to_send} {currency.symbol}\033[0m")
                    
                    if amount_to_send <= 0 and currency.symbol != 'BTC':
                        logger.warning(f"\033[93m⚠️ Amount to send {amount_to_send} {currency.symbol} is zero or negative\033[0m")
                        continue
                    
                    logger.info(f"\033[94m🚀 Consolidating {amount_to_send} {currency.symbol} from {user_wallet.deposit_address} to system wallet\033[0m")
                    
                    # Выполняем перевод с retry логикой
                    # Для TRC-20 токенов передаем contract_address
                    contract_address_for_send = currency.contract_address if currency.network and currency.network.upper() == 'TRC20' else None
                    
                    # ⚠️ ВАЖНО: Для TRC-20 токенов проверяем наличие TRX для оплаты газа
                    # Если TRX недостаточно, отправляем TRX с системного кошелька
                    if currency.network and currency.network.upper() == 'TRC20':
                        # Получаем баланс TRX на адресе пользователя (без contract_address для нативного TRX)
                        trx_balance = blockchain_service.get_balance(user_wallet.deposit_address)
                        min_trx_for_gas = Decimal('3')  # Минимум TRX для оплаты газа
                        
                        logger.info(f"\033[94m💎 TRX balance on address: {trx_balance} TRX (minimum required: {min_trx_for_gas} TRX)\033[0m")
                        
                        if trx_balance < min_trx_for_gas:
                            logger.warning(f"\033[93m⚠️ Insufficient TRX ({trx_balance} TRX) for gas on address {user_wallet.deposit_address}. Need to send TRX from system wallet.\033[0m")
                            
                            # Получаем системный TRX кошелек
                            try:
                                from .models import SystemWalletAddress
                                trx_currency = Cryptocurrency.objects.get(symbol='TRX', network='TRC20')
                                system_trx_wallet = SystemWalletAddress.objects.get(currency=trx_currency)
                                
                                # Проверяем баланс системного TRX кошелька
                                system_trx_balance = blockchain_service.get_balance(system_trx_wallet.address)
                                logger.info(f"\033[94m💎 System TRX wallet balance: {system_trx_balance} TRX\033[0m")
                                
                                # Рассчитываем необходимую сумму TRX для отправки
                                trx_amount_needed = min_trx_for_gas - trx_balance
                                
                                # Добавляем небольшой запас для надежности
                                trx_amount_to_send = trx_amount_needed + Decimal('1')
                                
                                # ⚠️ ВАЖНО: Учитываем комиссию за транзакцию TRX (обычно ~0.00001 TRX, но берем запас)
                                trx_transaction_fee = Decimal('0.1')  # Запас для комиссии транзакции TRX
                                total_trx_needed = trx_amount_to_send + trx_transaction_fee
                                
                                logger.info(f"\033[94m💸 Need to send {trx_amount_to_send} TRX + {trx_transaction_fee} TRX (fee) = {total_trx_needed} TRX total\033[0m")
                                
                                # Проверяем, достаточно ли TRX на системном кошельке
                                if system_trx_balance < total_trx_needed:
                                    logger.error(f"\033[91m❌ Insufficient TRX on system wallet! Balance: {system_trx_balance} TRX, needed: {total_trx_needed} TRX\033[0m")
                                    logger.error(f"\033[91m❌ Cannot send TRX for gas payment. Please top up system TRX wallet.\033[0m")
                                    continue
                                
                                # Отправляем TRX для оплаты газа
                                trx_service = get_blockchain_service('TRC20')
                                
                                logger.info(f"\033[94m💸 Sending {trx_amount_to_send} TRX from system wallet ({system_trx_wallet.address}) to {user_wallet.deposit_address} for gas payment\033[0m")
                                
                                # Используем приватный ключ системного TRX кошелька
                                system_trx_private_key = system_trx_wallet.private_key
                                
                                @retry_on_rpc_error(max_retries=3, delay=2, backoff=2)
                                def send_trx_for_gas():
                                    return trx_service.send_transaction(
                                        private_key=system_trx_private_key,
                                        to_address=user_wallet.deposit_address,
                                        amount=trx_amount_to_send,
                                    )
                                
                                gas_tx_hash = send_trx_for_gas()
                                logger.info(f"\033[92m✅ TRX gas payment sent successfully: {gas_tx_hash}\033[0m")
                                
                                # Ждем подтверждения TRX транзакции
                                logger.info(f"\033[94m⏳ Waiting 10 seconds for TRX transaction confirmation...\033[0m")
                                time.sleep(10)  # Ждем 10 секунд для подтверждения
                                
                                # Проверяем, что TRX действительно поступил
                                new_trx_balance = blockchain_service.get_balance(user_wallet.deposit_address)
                                logger.info(f"\033[94m💎 New TRX balance after transfer: {new_trx_balance} TRX\033[0m")
                                
                                if new_trx_balance < min_trx_for_gas:
                                    logger.warning(f"\033[93m⚠️ TRX balance still insufficient after transfer. Waiting additional 10 seconds...\033[0m")
                                    time.sleep(10)
                                    new_trx_balance = blockchain_service.get_balance(user_wallet.deposit_address)
                                    logger.info(f"\033[94m💎 TRX balance after additional wait: {new_trx_balance} TRX\033[0m")
                                
                            except Cryptocurrency.DoesNotExist:
                                logger.error(f"\033[91m❌ TRX currency not found in database. Cannot send TRX for gas payment.\033[0m")
                                continue
                            except SystemWalletAddress.DoesNotExist:
                                logger.error(f"\033[91m❌ System TRX wallet not found. Cannot send TRX for gas payment.\033[0m")
                                continue
                            except Exception as gas_error:
                                import traceback
                                error_trace = traceback.format_exc()
                                logger.error(f"\033[91m❌ Failed to send TRX for gas payment: {gas_error}\033[0m")
                                logger.error(f"\033[91m❌ Traceback: {error_trace}\033[0m")
                                continue
                        else:
                            logger.info(f"\033[92m✅ Sufficient TRX balance ({trx_balance} TRX) for gas payment\033[0m")
                    
                    @retry_on_rpc_error(max_retries=3, delay=2, backoff=2)
                    def send_consolidation_transaction():
                        # ⚠️ ВАЖНО: contract_address передаем только для TRC-20 и ERC-20 токенов
                        # Polygon (POL) не поддерживает contract_address в send_transaction
                        # Проверяем, поддерживает ли сервис contract_address
                        import inspect
                        sig = inspect.signature(blockchain_service.send_transaction)
                        params = list(sig.parameters.keys())
                        
                        if 'contract_address' in params and contract_address_for_send:
                            # Сервис поддерживает contract_address (Tron, Ethereum для ERC-20)
                            return blockchain_service.send_transaction(
                                private_key=private_key_input,
                                to_address=system_wallet_address,
                                amount=amount_to_send,
                                memo=f"consolidation_{user_wallet.user_id}",
                                contract_address=contract_address_for_send
                            )
                        else:
                            # Для нативных валют (POL, ETH native, BTC) не передаем contract_address
                            return blockchain_service.send_transaction(
                                private_key=private_key_input,
                                to_address=system_wallet_address,
                                amount=amount_to_send,
                                memo=f"consolidation_{user_wallet.user_id}"
                            )
                    
                    tx_hash = send_consolidation_transaction()
                    if not tx_hash:
                        logger.warning(f"\033[93m⚠️ No tx_hash returned for user {user_wallet.user.id}, skipping transaction creation.\033[0m")
                        continue
                    
                    logger.info(f"\033[92m✅ Transaction sent successfully: {tx_hash}\033[0m")
                    
                    # ⚠️ КРИТИЧЕСКИ ВАЖНО: Записываем транзакцию консолидации
                    # Для Bitcoin amount=0 означает sweep, поэтому сохраняем реальный баланс
                    # Для других валют amount_to_send - это реальная сумма, которая будет зачислена пользователю
                    consolidation_amount_to_save = amount_to_send if currency.symbol != 'BTC' else blockchain_balance
                    
                    # Для Bitcoin пересчитываем gas_cost после sweep (реальная разница между балансом и отправленной суммой)
                    if currency.symbol == 'BTC':
                        # После sweep реальный газ = баланс - отправленная сумма
                        # Но amount_to_send = 0 для sweep, поэтому используем оценку или пересчитываем
                        # В данном случае gas_cost уже рассчитан выше
                        pass
                    
                    with transaction.atomic():
                        Transaction.objects.create(
                            user=user_wallet.user,
                            crypto=currency,
                            amount=consolidation_amount_to_save,  # ⚠️ Это сумма, которая будет зачислена пользователю!
                            fee=gas_cost,  # ⚠️ ВАЖНО: Сохраняем реальную стоимость газа для учета комиссии
                            tx_hash=tx_hash,
                            type="consolidation",
                            status="pending",
                            timestamp=timezone.now()
                        )
                    
                    processed += 1
                    currency_processed += 1
                    logger.info(f"\033[92m💾 Consolidation transaction saved to DB: {tx_hash}\033[0m")
                    logger.info(f"\033[92m🎉 Successfully consolidated {consolidation_amount_to_save} {currency.symbol} for user {user_wallet.user.id} (wallet emptied)\033[0m")
                    
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

