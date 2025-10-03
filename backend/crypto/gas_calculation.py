"""
Модуль для расчета предполагаемой стоимости газа при депозитах
"""

from decimal import Decimal
from typing import Optional, Dict, Any
import logging

from .models import Cryptocurrency
from .blockchain.factory import get_blockchain_service
from .tasks_consolidation import get_gas_reserve, get_system_wallet_address

logger = logging.getLogger(__name__)


def calculate_estimated_gas_cost(currency: Cryptocurrency, deposit_amount: Decimal, user_address: str = None) -> Decimal:
    """
    Рассчитывает предполагаемую стоимость газа для депозита.
    
    Args:
        currency: Криптовалюта
        deposit_amount: Сумма депозита
        user_address: Адрес пользователя (опционально, для более точного расчета)
    
    Returns:
        Предполагаемая стоимость газа
    """
    try:
        # Для валют с мемо газ не нужен
        if currency.requires_memo:
            return Decimal('0')
        
        # Получаем сервис блокчейна
        blockchain_service = get_blockchain_service(currency.network or currency.symbol)
        
        # Метод 1: Умный расчет для валют с get_max_sendable_amount
        if hasattr(blockchain_service, 'get_max_sendable_amount') and user_address:
            try:
                system_wallet_address = get_system_wallet_address(currency)
                max_sendable = blockchain_service.get_max_sendable_amount(user_address, system_wallet_address)
                
                if max_sendable > 0:
                    # Получаем текущий баланс
                    current_balance = blockchain_service.get_balance(user_address)
                    gas_cost = current_balance - max_sendable
                    
                    # Если депозит увеличит баланс, пересчитываем газ
                    if deposit_amount > 0:
                        new_balance = current_balance + deposit_amount
                        # Оцениваем новый газ на основе увеличенного баланса
                        # Используем пропорциональный расчет
                        gas_cost = gas_cost * (new_balance / current_balance) if current_balance > 0 else gas_cost
                    
                    logger.info(f"Smart gas calculation for {currency.symbol}: {gas_cost}")
                    return max(Decimal('0'), gas_cost)
            except Exception as e:
                logger.warning(f"Smart gas calculation failed for {currency.symbol}: {e}")
        
        # Метод 2: Оценка газа для валют с estimate_gas_cost
        if hasattr(blockchain_service, 'estimate_gas_cost') and user_address:
            try:
                system_wallet_address = get_system_wallet_address(currency)
                
                # Конвертируем депозит в атомарные единицы для оценки
                if hasattr(blockchain_service, 'to_atomic_unit'):
                    deposit_atomic = blockchain_service.to_atomic_unit(deposit_amount, currency.decimals or 18)
                else:
                    deposit_atomic = int(deposit_amount * (10 ** (currency.decimals or 18)))
                
                gas_cost = blockchain_service.estimate_gas_cost(user_address, system_wallet_address, deposit_atomic)
                logger.info(f"Estimated gas cost for {currency.symbol}: {gas_cost}")
                return max(Decimal('0'), gas_cost)
            except Exception as e:
                logger.warning(f"Gas estimation failed for {currency.symbol}: {e}")
        
        # Метод 3: Фиксированный резерв (fallback)
        gas_reserve = get_gas_reserve(currency)
        logger.info(f"Using fixed gas reserve for {currency.symbol}: {gas_reserve}")
        return gas_reserve
        
    except Exception as e:
        logger.error(f"Failed to calculate gas cost for {currency.symbol}: {e}")
        # В случае ошибки возвращаем минимальный резерв
        return get_gas_reserve(currency)


def calculate_net_deposit_amount(currency: Cryptocurrency, deposit_amount: Decimal, user_address: str = None) -> Dict[str, Any]:
    """
    Рассчитывает чистую сумму депозита с учетом предполагаемой стоимости газа.
    
    Args:
        currency: Криптовалюта
        deposit_amount: Полная сумма депозита
        user_address: Адрес пользователя (опционально)
    
    Returns:
        Словарь с информацией о депозите:
        - net_amount: Чистая сумма для зачисления на баланс
        - gas_cost: Предполагаемая стоимость газа
        - gross_amount: Полная сумма депозита
    """
    try:
        # Для валют с мемо газ не нужен
        if currency.requires_memo:
            return {
                'net_amount': deposit_amount,
                'gas_cost': Decimal('0'),
                'gross_amount': deposit_amount,
                'calculation_method': 'no_gas_needed'
            }
        
        # Рассчитываем предполагаемую стоимость газа
        gas_cost = calculate_estimated_gas_cost(currency, deposit_amount, user_address)
        
        # Чистая сумма = полная сумма - газ
        net_amount = max(Decimal('0'), deposit_amount - gas_cost)
        
        return {
            'net_amount': net_amount,
            'gas_cost': gas_cost,
            'gross_amount': deposit_amount,
            'calculation_method': 'gas_deducted'
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate net deposit amount for {currency.symbol}: {e}")
        # В случае ошибки возвращаем полную сумму
        return {
            'net_amount': deposit_amount,
            'gas_cost': Decimal('0'),
            'gross_amount': deposit_amount,
            'calculation_method': 'error_fallback'
        }


def get_deposit_info_with_gas(currency: Cryptocurrency, deposit_amount: Decimal, user_address: str = None) -> Dict[str, Any]:
    """
    Получает полную информацию о депозите с учетом газа.
    
    Args:
        currency: Криптовалюта
        deposit_amount: Сумма депозита
        user_address: Адрес пользователя (опционально)
    
    Returns:
        Словарь с полной информацией о депозите
    """
    deposit_info = calculate_net_deposit_amount(currency, deposit_amount, user_address)
    
    # Добавляем дополнительную информацию
    deposit_info.update({
        'currency_symbol': currency.symbol,
        'currency_network': currency.network,
        'requires_memo': currency.requires_memo,
        'decimals': currency.decimals
    })
    
    return deposit_info


def calculate_withdrawal_gas_cost(currency: Cryptocurrency, withdrawal_amount: Decimal, destination_address: str = None) -> Decimal:
    """
    Рассчитывает стоимость газа для вывода средств.
    
    Args:
        currency: Криптовалюта
        withdrawal_amount: Сумма вывода
        destination_address: Адрес получателя (опционально, для более точного расчета)
    
    Returns:
        Стоимость газа для вывода
    """
    try:
        # Для валют с мемо газ обычно не нужен (системный кошелек)
        if currency.requires_memo:
            return Decimal('0')
        
        # Получаем сервис блокчейна
        blockchain_service = get_blockchain_service(currency.network or currency.symbol)
        
        # Метод 1: Умный расчет для валют с get_max_sendable_amount
        if hasattr(blockchain_service, 'get_max_sendable_amount') and destination_address:
            try:
                # Получаем адрес системного кошелька
                from .tasks_consolidation import get_system_wallet_address
                system_wallet_address = get_system_wallet_address(currency)
                
                # Рассчитываем максимальную отправляемую сумму
                max_sendable = blockchain_service.get_max_sendable_amount(system_wallet_address, destination_address)
                
                if max_sendable > 0:
                    # Получаем текущий баланс системного кошелька
                    current_balance = blockchain_service.get_balance(system_wallet_address)
                    gas_cost = current_balance - max_sendable
                    
                    logger.info(f"Smart withdrawal gas calculation for {currency.symbol}: {gas_cost}")
                    return max(Decimal('0'), gas_cost)
            except Exception as e:
                logger.warning(f"Smart withdrawal gas calculation failed for {currency.symbol}: {e}")
        
        # Метод 2: Оценка газа для валют с estimate_gas_cost
        if hasattr(blockchain_service, 'estimate_gas_cost') and destination_address:
            try:
                from .tasks_consolidation import get_system_wallet_address
                system_wallet_address = get_system_wallet_address(currency)
                
                # Конвертируем сумму вывода в атомарные единицы для оценки
                if hasattr(blockchain_service, 'to_atomic_unit'):
                    withdrawal_atomic = blockchain_service.to_atomic_unit(withdrawal_amount, currency.decimals or 18)
                else:
                    withdrawal_atomic = int(withdrawal_amount * (10 ** (currency.decimals or 18)))
                
                gas_cost = blockchain_service.estimate_gas_cost(system_wallet_address, destination_address, withdrawal_atomic)
                logger.info(f"Estimated withdrawal gas cost for {currency.symbol}: {gas_cost}")
                return max(Decimal('0'), gas_cost)
            except Exception as e:
                logger.warning(f"Withdrawal gas estimation failed for {currency.symbol}: {e}")
        
        # Метод 3: Фиксированный резерв (fallback)
        gas_reserve = get_gas_reserve(currency)
        logger.info(f"Using fixed withdrawal gas reserve for {currency.symbol}: {gas_reserve}")
        return gas_reserve
        
    except Exception as e:
        logger.error(f"Failed to calculate withdrawal gas cost for {currency.symbol}: {e}")
        # В случае ошибки возвращаем минимальный резерв
        return get_gas_reserve(currency)


def calculate_max_withdrawal_amount(currency: Cryptocurrency, user_balance: Decimal, destination_address: str = None) -> Dict[str, Any]:
    """
    Рассчитывает максимальную сумму вывода с учетом газа.
    
    Args:
        currency: Криптовалюта
        user_balance: Баланс пользователя
        destination_address: Адрес получателя (опционально)
    
    Returns:
        Словарь с информацией о максимальном выводе:
        - max_withdrawal: Максимальная сумма для вывода
        - gas_cost: Стоимость газа
        - total_required: Общая сумма (вывод + газ)
    """
    try:
        # Для валют с мемо газ не нужен
        if currency.requires_memo:
            return {
                'max_withdrawal': user_balance,
                'gas_cost': Decimal('0'),
                'total_required': user_balance,
                'calculation_method': 'no_gas_needed'
            }
        
        # Рассчитываем стоимость газа
        gas_cost = calculate_withdrawal_gas_cost(currency, user_balance, destination_address)
        
        # Максимальная сумма вывода = баланс - газ
        max_withdrawal = max(Decimal('0'), user_balance - gas_cost)
        
        return {
            'max_withdrawal': max_withdrawal,
            'gas_cost': gas_cost,
            'total_required': max_withdrawal + gas_cost,
            'calculation_method': 'gas_deducted'
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate max withdrawal amount for {currency.symbol}: {e}")
        # В случае ошибки возвращаем полный баланс
        return {
            'max_withdrawal': user_balance,
            'gas_cost': Decimal('0'),
            'total_required': user_balance,
            'calculation_method': 'error_fallback'
        }


def calculate_withdrawal_total_cost(currency: Cryptocurrency, withdrawal_amount: Decimal, destination_address: str = None) -> Dict[str, Any]:
    """
    Рассчитывает общую стоимость вывода (сумма + газ + комиссия).
    
    Args:
        currency: Криптовалюта
        withdrawal_amount: Сумма вывода
        destination_address: Адрес получателя (опционально)
    
    Returns:
        Словарь с информацией о стоимости вывода
    """
    try:
        # Рассчитываем стоимость газа
        gas_cost = calculate_withdrawal_gas_cost(currency, withdrawal_amount, destination_address)
        
        # Рассчитываем комиссию платформы
        platform_fee = (withdrawal_amount * currency.fee_percentage) / Decimal('100')
        
        # Общая стоимость = сумма + газ + комиссия
        total_cost = withdrawal_amount + gas_cost + platform_fee
        
        return {
            'withdrawal_amount': withdrawal_amount,
            'gas_cost': gas_cost,
            'platform_fee': platform_fee,
            'total_cost': total_cost,
            'currency_symbol': currency.symbol,
            'calculation_method': 'with_gas_and_fees'
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate withdrawal total cost for {currency.symbol}: {e}")
        # В случае ошибки возвращаем только сумму и комиссию
        platform_fee = (withdrawal_amount * currency.fee_percentage) / Decimal('100')
        return {
            'withdrawal_amount': withdrawal_amount,
            'gas_cost': Decimal('0'),
            'platform_fee': platform_fee,
            'total_cost': withdrawal_amount + platform_fee,
            'currency_symbol': currency.symbol,
            'calculation_method': 'error_fallback'
        }
