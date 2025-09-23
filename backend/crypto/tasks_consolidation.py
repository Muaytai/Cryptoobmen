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
    }
    return minimums.get(currency.symbol, Decimal('0.001'))

def get_gas_reserve(currency: Cryptocurrency) -> Decimal:
    """Резерв для покрытия комиссии газа в зависимости от валюты"""
    reserves = {
        'POL': Decimal('0.01'),    # Снижено после введения динамического расчёта
        'BTC': Decimal('0.00005'), 
        'ETH': Decimal('0.005'),
        'TRX': Decimal('5'),
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
                    platform_fee = Decimal('0')  # TODO: Платформенная комиссия (будет реализована позже)
                    total_fees = gas_fee + platform_fee
                    
                    # Списываем только комиссии с баланса пользователя
                    if total_fees > 0:
                        user_wallet.balance -= total_fees
                        user_wallet.available_balance = user_wallet.balance - user_wallet.locked_balance
                        user_wallet.save()
                        logger.info(f"Deducted fees from user {tx.user.id}: gas={gas_fee}, platform={platform_fee}, total={total_fees}")
                    
                    logger.info(f"Consolidation confirmed: {tx.tx_hash} for {tx.amount} {tx.crypto.symbol} - funds secured, user balance preserved (fees: {total_fees})")
                    confirmed += 1
                    
                    # ПРИМЕЧАНИЕ: Новый адрес уже сгенерирован при отправке консолидации в process_pending_deposits
                    # Здесь генерация адреса больше не нужна
                    
        except Exception as e:
            logger.error(f"Error checking consolidation confirmation for {tx.tx_hash}: {e}")
            continue
    
    logger.info(f"Consolidation confirmations checked. Confirmed: {confirmed}")
    return f"Checked consolidation confirmations: {confirmed} confirmed"