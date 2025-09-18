from __future__ import annotations

import os
import logging
import traceback
from decimal import Decimal
from celery import shared_task
from celery.utils.log import get_task_logger
from crypto.blockchain.xrp import XRPService
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

    # Обрабатываем все системные кошельки
    for wallet in SystemWalletAddress.objects.select_related('currency').all():
        currency = wallet.currency
        if not currency.is_active:
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
            # Получаем последнюю транзакцию для КОНКРЕТНОГО пользователя
            last_tx = Transaction.objects.filter(
                user=user_wallet.user,
                crypto=currency,
                tx_hash__isnull=False
            ).order_by("-timestamp").first()
            min_ts = int(last_tx.timestamp.timestamp() * 1000) if last_tx else 0
            logger.info(f"[no-memo][DEBUG] CALL get_transactions: address={address}, min_ts={min_ts}, contract={currency.contract_address}")
            
            # Для Ethereum и ERC-20 токенов передаем contract_address
            if currency.network and currency.network.upper() == 'ERC20':
                raw_transactions = service.get_transactions(
                    address=address,
                    min_timestamp=min_ts,
                    contract_address=currency.contract_address
                )
            else:
                raw_transactions = service.get_transactions(address=address, min_timestamp=min_ts)
            
            logger.info(f"[no-memo] Found {len(raw_transactions)} tx for {currency.symbol} address {address}")
            for ev in raw_transactions:
                tx_hash = ev.get("transaction_id")
                amount_str = ev.get("value")
                logger.info(f"[no-memo] Processing: {currency.symbol} {address} tx={tx_hash} amount={amount_str}")
                existing_tx = Transaction.objects.filter(tx_hash=tx_hash, user=user_wallet.user).first()
                if existing_tx:
                    logger.warning(f"[no-memo] Duplicate tx {tx_hash} for user {user_wallet.user.id}. Re-sending signal.")
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
                        logger.info(f"[no-memo] Re-sent WebSocket signal for address {address}")
                    except Exception as e:
                        logger.error(f"[no-memo] Failed to re-send WebSocket signal for address {address}: {e}")
                    continue
                try:
                    # Для Ethereum используем правильное количество десятичных знаков
                    if currency.network and currency.network.upper() == 'ERC20':
                        if currency.symbol == 'ETH':
                            # ETH в Wei (18 decimals)
                            amount = Decimal(amount_str) / Decimal(10**18)
                        else:
                            # ERC-20 токены используют свои decimals
                            amount = Decimal(amount_str) / Decimal(10**currency.decimals)
                    else:
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
    return f"Готово, обработано: {processed}"


@shared_task(bind=True, name='crypto.tasks.process_withdrawal')
def process_withdrawal(self, withdrawal_id: int) -> str:
    logger.info(f"--- Starting processing for withdrawal_id: {withdrawal_id} ---")
    from transactions.models import Withdrawal
    from .models import CommissionWallet, CommissionTransaction

    withdrawal = None
    try:
        # Используем одну транзакцию БД для всех проверок и начальных изменений
        with transaction.atomic():
            # Получаем все связанные объекты одним запросом
            withdrawal = Withdrawal.objects.select_related(
                'transaction', 'wallet', 'user', 'transaction__crypto'
            ).get(id=withdrawal_id)

            if withdrawal.transaction.status not in ['pending', 'processing']:
                logger.warning(f"Withdrawal {withdrawal_id} is not pending or processing. Status: {withdrawal.transaction.status}")
                return f"skip:not_pending"

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

            # Меняем статус на "в обработке" перед отправкой в сеть
            withdrawal.transaction.status = 'processing'
            withdrawal.transaction.save()

        # --- Отправка в блокчейн (вне транзакции БД) ---
        network = crypto.network
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
        
        if network.upper() == 'ERC20':
            tx_kwargs['contract_address'] = crypto.contract_address

        tx_hash = service.send_transaction(**tx_kwargs)

        # --- Финализация в БД после успешной отправки ---
        with transaction.atomic():
            # Обновляем основную транзакцию
            withdrawal.transaction.tx_hash = tx_hash
            withdrawal.transaction.status = 'awaiting_network_confirmation'
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
            withdrawal.transaction.status = 'failed'
            withdrawal.transaction.notes = f"Transaction error: {str(e)}"
            withdrawal.transaction.save()
        return f"error:transaction_failed - {str(e)}"


@shared_task
def process_pending_withdrawals():
    """
    Периодическая задача для обработки всех ожидающих или зависших заявок на вывод.
    Находит выводы, которые подтверждены по email, но не завершены,
    и перезапускает для них задачу обработки.
    """
    from transactions.models import Withdrawal
    from django.db.models import Q

    stuck_withdrawals = Withdrawal.objects.filter(
        Q(transaction__status='pending') | Q(transaction__status='processing'),
        is_email_confirmed=True
    )
    
    logger.info(f"Found {stuck_withdrawals.count()} stuck withdrawals to process.")

    for withdrawal in stuck_withdrawals:
        logger.info(f"Re-queueing processing for withdrawal {withdrawal.id}")
        process_withdrawal.delay(withdrawal.id)

@shared_task
def process_pending_deposits():
    """
    Периодическая задача для обработки всех ожидающих депозитов (если требуется).
    """
    # Здесь можно реализовать обработку зависших депозитов, если такая логика нужна
    pass

@shared_task(bind=True, max_retries=20, default_retry_delay=60)
def check_withdrawal_confirmation(self, withdrawal_id: int):
    """
    Проверяет подтверждение транзакции вывода в блокчейне.
    """
    from transactions.models import Withdrawal

    withdrawal = None
    try:
        withdrawal = Withdrawal.objects.select_related('transaction', 'wallet', 'user').get(id=withdrawal_id)
        
        if withdrawal.transaction.status != 'awaiting_network_confirmation':
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
        is_confirmed = service.is_transaction_confirmed(tx_hash)

        if is_confirmed:
            logger.info(f"Withdrawal {withdrawal_id} (tx: {tx_hash}) is confirmed on the blockchain.")
            # Сумма для списания = отправленная сумма + комиссия
            amount_to_withdraw = withdrawal.transaction.amount + withdrawal.transaction.fee
            
            with transaction.atomic():
                # Блокируем кошелек для безопасного списания
                user_wallet = UserWallet.objects.select_for_update().get(id=withdrawal.wallet.id)
                
                # Повторная проверка баланса на всякий случай
                if user_wallet.balance < amount_to_withdraw:
                    withdrawal.transaction.status = 'failed'
                    withdrawal.transaction.notes = "Insufficient funds discovered upon withdrawal confirmation."
                    withdrawal.transaction.save()
                    logger.error(f"Insufficient funds for withdrawal {withdrawal.id} upon confirmation. Balance: {user_wallet.balance}, required: {amount_to_withdraw}")
                    return "error:insufficient_funds_on_confirmation"

                # Списываем средства
                user_wallet.balance -= amount_to_withdraw
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
            # Увеличиваем задержку с каждой попыткой, как указано в требованиях
            retry_countdown = 60 * (self.request.retries + 1)
            self.retry(countdown=retry_countdown, max_retries=20)

    except Withdrawal.DoesNotExist:
        logger.error(f"Withdrawal with id {withdrawal_id} not found for confirmation check.")
        return f"error:not_found"
    except Exception as e:
        logger.error(f"Error checking confirmation for withdrawal {withdrawal_id}: {e}", exc_info=True)
        try:
            # Если после нескольких попыток возникает ошибка, помечаем как failed
            if self.request.retries >= self.max_retries:
                 if withdrawal:
                    withdrawal.transaction.status = 'failed'
                    withdrawal.transaction.notes = f"Failed to confirm transaction after multiple retries: {str(e)}"
                    withdrawal.transaction.save()
                 return f"error:max_retries_exceeded"
            self.retry(exc=e)
        except Exception as retry_exc:
             logger.error(f"Failed to retry task for withdrawal {withdrawal_id}: {retry_exc}", exc_info=True)
             if withdrawal:
                withdrawal.transaction.status = 'failed'
                withdrawal.transaction.notes = f"Critical error during confirmation check: {str(e)}"
                withdrawal.transaction.save()
             return f"error:critical_failure"
