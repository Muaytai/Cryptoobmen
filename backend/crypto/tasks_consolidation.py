"""
Задачи консолидации средств - автоматический перевод депозитов на системный кошелек
"""
from __future__ import annotations

import logging
from decimal import Decimal
from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from django.db import transaction

from .models import UserWallet, Cryptocurrency
from .blockchain.factory import get_blockchain_service
from transactions.models import Transaction

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


@shared_task
def consolidate_user_deposits():
    """
    Консолидация депозитов - перевод средств с пользовательских адресов на системный кошелек.
    Работает только для валют без MEMO (POL, BTC, ETH).
    """
    processed = 0
    logger.info("[consolidate_user_deposits] Starting consolidation...")
    
    # Получаем все активные валюты без MEMO
    currencies_no_memo = Cryptocurrency.objects.filter(
        is_active=True, 
        requires_memo=False
    )
    
    for currency in currencies_no_memo:
        logger.info(f"Processing consolidation for {currency.symbol}")
        
        try:
            # Получаем системный кошелек
            system_wallet = UserWallet.objects.get(
                user=None,
                currency=currency,
                is_system_wallet=True,
                is_active=True
            )
            
            if not system_wallet.encrypted_private_key:
                logger.warning(f"System wallet for {currency.symbol} has no private key, skipping")
                continue
                
            # Получаем все пользовательские кошельки с балансом на блокчейне
            user_wallets = UserWallet.objects.filter(
                currency=currency,
                is_system_wallet=False,
                deposit_address__isnull=False,
                encrypted_private_key__isnull=False  # Только кошельки с приватными ключами
            ).exclude(deposit_address='')
            
            blockchain_service = get_blockchain_service(currency.network or currency.symbol)
            
            for user_wallet in user_wallets:
                try:
                    # Проверяем баланс на блокчейне
                    blockchain_balance = blockchain_service.get_balance(user_wallet.deposit_address)
                    
                    # Минимальная сумма для консолидации (чтобы покрыть комиссию)
                    min_consolidation_amount = get_min_consolidation_amount(currency)
                    
                    if blockchain_balance < min_consolidation_amount:
                        logger.debug(f"Balance {blockchain_balance} {currency.symbol} on {user_wallet.deposit_address} too small for consolidation")
                        continue
                    
                    # Рассчитываем сумму к переводу (оставляем немного на комиссию)
                    gas_reserve = get_gas_reserve(currency)
                    amount_to_send = blockchain_balance - gas_reserve
                    
                    if amount_to_send <= 0:
                        logger.debug(f"Amount to send {amount_to_send} {currency.symbol} is zero or negative after gas reserve")
                        continue
                    
                    logger.info(f"Consolidating {amount_to_send} {currency.symbol} from {user_wallet.deposit_address} to system wallet")
                    
                    # Выполняем перевод
                    try:
                        logger.info(f"Attempting to send transaction from {user_wallet.deposit_address} to {get_system_wallet_address(currency)}")
                        tx_hash = blockchain_service.send_transaction(
                            private_key_input=user_wallet.encrypted_private_key,
                            to_address=get_system_wallet_address(currency),
                            amount=amount_to_send,
                            memo=f"consolidation_{user_wallet.user_id}"
                        )
                        
                        logger.info(f"Transaction sent successfully with hash: {tx_hash}")
                        
                        # Записываем транзакцию консолидации
                        try:
                            with transaction.atomic():
                                tx = Transaction.objects.create(
                                    user=user_wallet.user,
                                    crypto=currency,
                                    amount=amount_to_send,
                                    tx_hash=tx_hash,
                                    type="consolidation",
                                    status="pending",
                                    timestamp=timezone.now()
                                )
                                logger.info(f"Transaction record created in database with ID: {tx.id}")
                        except Exception as db_error:
                            logger.error(f"Failed to create transaction record in database: {db_error}", exc_info=True)
                            raise
                        
                        processed += 1
                        logger.info(f"Consolidation transaction created: {tx_hash}")
                    except Exception as tx_error:
                        logger.error(f"Failed to send transaction: {tx_error}", exc_info=True)
                        raise
                    
                except Exception as e:
                    logger.error(f"Error consolidating {currency.symbol} for user {user_wallet.user_id}: {e}")
                    continue
                    
        except UserWallet.DoesNotExist:
            logger.warning(f"System wallet for {currency.symbol} not found")
            continue
        except Exception as e:
            logger.error(f"Error processing currency {currency.symbol}: {e}")
            continue
    
    logger.info(f"[consolidate_user_deposits] Processed {processed} consolidations")
    return f"Consolidation completed: {processed} transactions"


def get_min_consolidation_amount(currency: Cryptocurrency) -> Decimal:
    """Минимальная сумма для консолидации в зависимости от валюты"""
    minimums = {
        'POL': Decimal('0.01'),    # Снижен порог для testnet (было 0.1)
        'ETH': Decimal('0.001'), 
        'BTC': Decimal('0.0001'),
        'SOL': Decimal('0.01'),    # 0.01 SOL минимум для консолидации
    }
    return minimums.get(currency.symbol, Decimal('0.01'))


def get_gas_reserve(currency: Cryptocurrency) -> Decimal:
    """Резерв на газ в зависимости от валюты"""
    reserves = {
        'POL': Decimal('0.005'),   # Снижен резерв для testnet (было 0.01)
        'ETH': Decimal('0.0001'), # ~20 Gwei * 21000 gas  
        'BTC': Decimal('0.00001'), # ~1000 sat
        'SOL': Decimal('0.002'),   # 0.002 SOL резерв на комиссию (~0.000005 SOL за транзакцию)
    }
    return reserves.get(currency.symbol, Decimal('0.001'))


def get_system_wallet_address(currency: Cryptocurrency) -> str:
    """Получить адрес системного кошелька для валюты"""
    try:
        system_wallet = UserWallet.objects.get(
            user=None,
            currency=currency,
            is_system_wallet=True,
            is_active=True
        )
        
        # Для валют без MEMO системный кошелек тоже имеет deposit_address
        if system_wallet.deposit_address:
            return system_wallet.deposit_address
            
        # Если нет deposit_address, генерируем новый
        blockchain_service = get_blockchain_service(currency.network or currency.symbol)
        address, private_key = blockchain_service.create_new_address()
        
        system_wallet.deposit_address = address
        system_wallet.encrypted_private_key = private_key
        system_wallet.save()
        
        logger.info(f"Generated new system wallet address for {currency.symbol}: {address}")
        return address
        
    except UserWallet.DoesNotExist:
        raise ValueError(f"System wallet for {currency.symbol} not found")


@shared_task
def check_consolidation_confirmations():
    """
    Проверяет подтверждения транзакций консолидации и обновляет балансы
    """
    pending_consolidations = Transaction.objects.filter(
        type="consolidation",
        status="pending"
    )
    
    confirmed = 0
    
    for tx in pending_consolidations:
        try:
            blockchain_service = get_blockchain_service(tx.crypto.network or tx.crypto.symbol)
            
            # Проверяем подтверждение транзакции
            is_confirmed = blockchain_service.is_transaction_confirmed(tx.tx_hash)
            
            if is_confirmed:
                with transaction.atomic():
                    # Обновляем статус транзакции
                    tx.status = "completed"
                    tx.save()
                    
                    # КРИТИЧЕСКИ ВАЖНО: Списываем средства с баланса пользователя
                    user_wallet = UserWallet.objects.select_for_update().get(
                        user=tx.user,
                        currency=tx.crypto
                    )
                    user_wallet.balance -= tx.amount
                    user_wallet.save()
                    
                    logger.info(f"Consolidation confirmed: {tx.tx_hash} for {tx.amount} {tx.crypto.symbol}, balance updated for user {tx.user.id}")
                    confirmed += 1
                    
        except Exception as e:
            logger.error(f"Error checking consolidation confirmation for {tx.tx_hash}: {e}")
            continue
    
    logger.info(f"Confirmed {confirmed} consolidation transactions")
    return f"Confirmed consolidations: {confirmed}"
