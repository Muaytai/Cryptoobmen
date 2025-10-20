
"""
Задачи консолидации средств - вспомогательные функции и проверка подтверждений
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


def get_min_consolidation_amount(currency: Cryptocurrency) -> Decimal:
    """Минимальная сумма для консолидации в зависимости от валюты"""
    minimums = {
        'POL': Decimal('0.01'),    # Снижено - теперь используем динамический расчёт газа
        'BTC': Decimal('0.0001'),
        'ETH': Decimal('0.01'),
        'TRX': Decimal('10'),
        'SOL': Decimal('0.01'),    # Минимум для SOL (с запасом комиссии сети)
    }
    return minimums.get(currency.symbol, Decimal('0.001'))

def get_gas_reserve(currency: Cryptocurrency) -> Decimal:
    """Резерв для покрытия комиссии газа в зависимости от валюты"""
    reserves = {
        'POL': Decimal('0.01'),    # Снижено после введения динамического расчёта
        'BTC': Decimal('0.00005'), 
        'ETH': Decimal('0.005'),
        'TRX': Decimal('5'),
        'SOL': Decimal('0.002'),   # Резерв под комиссии Solana (~несколько тысяч лампортов)
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
    logger.info("Checking consolidation confirmations...")
    
    # Находим все ожидающие подтверждения консолидации
    pending_consolidations = Transaction.objects.filter(
        type="consolidation",
        status="pending"
    )
    
    confirmed = 0
    
    for tx in pending_consolidations:
        try:
            service = get_blockchain_service(tx.crypto.network or tx.crypto.symbol)
            
            # Проверяем подтверждение транзакции
            is_confirmed = service.is_transaction_confirmed(tx.tx_hash)
            
            if is_confirmed:
                with transaction.atomic():
                    # Обновляем статус транзакции
                    tx.status = "completed"
                    tx.save()
                    
                    # КОНСОЛИДАЦИЯ НЕ СПИСЫВАЕТ средства с баланса пользователя!
                    # Это внутренний перевод для безопасности, средства остаются у пользователя
                    # Списываем только реальные комиссии (газ + платформенные)
                    
                    # Получаем кошелек пользователя для списания комиссий
                    user_wallet = UserWallet.objects.get(
                        user=tx.user,
                        currency=tx.crypto,
                        is_system_wallet=False
                    )
                    
                    # Рассчитываем реальные комиссии
                    gas_fee = tx.fee if tx.fee else Decimal('0')  # Комиссия за газ (уже записана в транзакции)
                    
                    # Платформенная комиссия за консолидацию (процент от суммы депозита)
                    platform_fee_percentage = tx.crypto.fee_percentage or Decimal('0.2')  # По умолчанию 0.2%
                    platform_fee = (tx.amount * platform_fee_percentage) / Decimal('100')
                    
                    total_fees = gas_fee + platform_fee
                    
                    # Списываем только комиссии с баланса пользователя
                    if total_fees > 0:
                        user_wallet.balance -= total_fees
                        user_wallet.available_balance = user_wallet.balance - user_wallet.locked_balance
                        user_wallet.save()
                        logger.info(f"Deducted fees from user {tx.user.id}: gas={gas_fee}, platform={platform_fee}, total={total_fees}")
                        
                        # Начисляем платформенную комиссию на CommissionWallet
                        if platform_fee > 0:
                            from .models import CommissionWallet, CommissionTransaction
                            
                            commission_wallet, _ = CommissionWallet.objects.get_or_create(currency=tx.crypto)
                            commission_wallet.balance += platform_fee
                            commission_wallet.save()
                            
                            # Логируем транзакцию комиссии
                            CommissionTransaction.objects.create(
                                user=tx.user,
                                currency=tx.crypto,
                                amount=platform_fee,
                                commission_type='consolidation',
                                related_object_id=str(tx.id)
                            )
                            
                            logger.info(f"Platform fee {platform_fee} {tx.crypto.symbol} added to commission wallet")
                        
                        # Обновляем баланс пользователя с учетом зачисленного депозита минус комиссии
                        # Депозит уже был зачислен ранее, теперь списываем только комиссии
                        logger.info(f"User {tx.user.id} balance after consolidation: {user_wallet.balance} {tx.crypto.symbol} (deposit: {tx.amount}, fees deducted: {total_fees})")
                    
                    logger.info(f"Consolidation confirmed: {tx.tx_hash} for {tx.amount} {tx.crypto.symbol} - funds secured, user balance preserved (fees: {total_fees})")
                    
                    # Логирование/синхронизацию баланса системного кошелька для SOL выполняем ПОСЛЕ коммита,
                    # чтобы внешние ошибки не откатывали изменение статуса транзакции.
                    if tx.crypto.symbol.upper() == 'SOL' or (tx.crypto.network or '').lower() == 'solana':
                        currency_id = tx.crypto_id
                        tx_id = tx.id
                        tx_amount = tx.amount
                        tx_symbol = tx.crypto.symbol
                        post_commit_notes = f'Consolidation confirmed: {tx_amount} {tx_symbol}, total fees: {total_fees}'

                        def _log_system_balance_after_commit():
                            try:
                                from django.db import connection  # ensures Django app registry is ready
                                from .models import SystemWalletBalanceLog, Cryptocurrency
                                from .tasks_consolidation import get_system_wallet_address
                                from .blockchain.factory import get_blockchain_service
                                from transactions.models import Transaction as TxModel

                                currency = Cryptocurrency.objects.get(id=currency_id)
                                tx_obj = TxModel.objects.get(id=tx_id)

                                # Получаем сервис заново, чтобы не зависеть от контекста задачи/соединения
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
                    
                    confirmed += 1
                    
                    # ПРИМЕЧАНИЕ: Новый адрес уже сгенерирован при отправке консолидации в process_pending_deposits
                    # Здесь генерация адреса больше не нужна
                    
        except Exception as e:
            logger.error(f"Error checking consolidation confirmation for {tx.tx_hash}: {e}")
            continue
    
    logger.info(f"Consolidation confirmations checked. Confirmed: {confirmed}")
    return f"Checked consolidation confirmations: {confirmed} confirmed"

