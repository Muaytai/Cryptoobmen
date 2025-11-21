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
                
                # Получаем текущий баланс
                current_balance = blockchain_service.get_balance(user_address)
                
                # ⚠️ ВАЖНО: Для ETH и других нативных валют газ не зависит от суммы транзакции
                # Используем текущий баланс для расчета максимальной отправляемой суммы
                # Это дает точную оценку газа, которая будет использована при консолидации
                if current_balance > 0:
                    max_sendable = blockchain_service.get_max_sendable_amount(user_address, system_wallet_address)
                    gas_cost = current_balance - max_sendable
                    
                    logger.info(f"Smart gas calculation for {currency.symbol}: balance={current_balance}, max_sendable={max_sendable}, gas_cost={gas_cost}")
                    return max(Decimal('0'), gas_cost)
                else:
                    # Если баланс 0, используем оценку газа для будущего депозита
                    # Для ETH газ фиксированный (~21000 gas units), не зависит от суммы
                    # Используем estimate_gas_cost с нулевой суммой для оценки базового газа
                    if hasattr(blockchain_service, 'estimate_gas_cost'):
                        try:
                            gas_cost = blockchain_service.estimate_gas_cost(user_address, system_wallet_address, 0)
                            logger.info(f"Gas estimation for {currency.symbol} with zero balance: {gas_cost}")
                            return max(Decimal('0'), gas_cost)
                        except Exception:
                            pass
                    
                    # Fallback: используем резерв газа
                    gas_reserve = get_gas_reserve(currency)
                    logger.info(f"Using gas reserve for {currency.symbol} (zero balance): {gas_reserve}")
                    return gas_reserve
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
    Рассчитывает максимальную сумму вывода с учетом газа и комиссии платформы.
    
    ⚠️ ВАЖНО: Учитывает:
    - Стоимость газа
    - Комиссию платформы (fee_percentage)
    - Общая сумма должна укладываться в баланс пользователя
    
    Args:
        currency: Криптовалюта
        user_balance: Баланс пользователя
        destination_address: Адрес получателя (опционально)
    
    Returns:
        Словарь с информацией о максимальном выводе:
        - max_withdrawal: Максимальная сумма для вывода
        - gas_cost: Стоимость газа
        - platform_fee: Комиссия платформы
        - total_required: Общая сумма (вывод + газ + комиссия)
    """
    try:
        # Для валют с мемо газ не нужен
        if currency.requires_memo:
            # Для валют с мемо все еще может быть комиссия платформы
            fee_percentage = getattr(currency, 'fee_percentage', Decimal('0'))
            if fee_percentage > 0:
                # max_withdrawal * (1 + fee_percentage / 100) <= user_balance
                max_withdrawal = user_balance / (Decimal('1') + fee_percentage / Decimal('100'))
                platform_fee = max_withdrawal * fee_percentage / Decimal('100')
            else:
                max_withdrawal = user_balance
                platform_fee = Decimal('0')
            
            return {
                'max_withdrawal': max_withdrawal,
                'gas_cost': Decimal('0'),
                'platform_fee': platform_fee,
                'total_required': max_withdrawal + platform_fee,
                'calculation_method': 'no_gas_needed'
            }
        
        # Получаем процент комиссии платформы
        fee_percentage = getattr(currency, 'fee_percentage', Decimal('0'))
        
        # ⚠️ ВАЖНО: Используем итеративный подход для точного расчета
        # Газ может зависеть от суммы вывода, поэтому нужно найти правильный баланс
        # Уравнение: max_withdrawal + gas_cost + platform_fee <= user_balance
        # где platform_fee = max_withdrawal * fee_percentage / 100
        
        # Начальное приближение: предполагаем, что газ фиксированный
        # Используем оценку газа на основе баланса
        estimated_gas = calculate_withdrawal_gas_cost(currency, user_balance, destination_address)
        
        # Первое приближение: max_withdrawal = (user_balance - gas) / (1 + fee_percentage / 100)
        if fee_percentage > 0:
            max_withdrawal = (user_balance - estimated_gas) / (Decimal('1') + fee_percentage / Decimal('100'))
        else:
            max_withdrawal = user_balance - estimated_gas
        
        max_withdrawal = max(Decimal('0'), max_withdrawal)
        
        # Уточняем расчет газа на основе полученной суммы
        if max_withdrawal > 0:
            gas_cost = calculate_withdrawal_gas_cost(currency, max_withdrawal, destination_address)
            
            # Пересчитываем с учетом реального газа
            if fee_percentage > 0:
                max_withdrawal = (user_balance - gas_cost) / (Decimal('1') + fee_percentage / Decimal('100'))
            else:
                max_withdrawal = user_balance - gas_cost
            
            max_withdrawal = max(Decimal('0'), max_withdrawal)
        
        # Рассчитываем комиссию платформы
        platform_fee = max_withdrawal * fee_percentage / Decimal('100') if fee_percentage > 0 else Decimal('0')
        
        # Общая требуемая сумма
        total_required = max_withdrawal + gas_cost + platform_fee
        
        # Проверяем, что все укладывается в баланс
        if total_required > user_balance:
            # Если не укладывается, уменьшаем сумму вывода
            if fee_percentage > 0:
                max_withdrawal = (user_balance - gas_cost) / (Decimal('1') + fee_percentage / Decimal('100'))
            else:
                max_withdrawal = user_balance - gas_cost
            max_withdrawal = max(Decimal('0'), max_withdrawal)
            platform_fee = max_withdrawal * fee_percentage / Decimal('100') if fee_percentage > 0 else Decimal('0')
            total_required = max_withdrawal + gas_cost + platform_fee
        
        logger.info(f"Max withdrawal calculation for {currency.symbol}: balance={user_balance}, max_withdrawal={max_withdrawal}, gas={gas_cost}, fee={platform_fee}, total={total_required}")
        
        return {
            'max_withdrawal': max_withdrawal,
            'gas_cost': gas_cost,
            'platform_fee': platform_fee,
            'total_required': total_required,
            'calculation_method': 'gas_and_fee_deducted'
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate max withdrawal amount for {currency.symbol}: {e}")
        # В случае ошибки возвращаем полный баланс
        return {
            'max_withdrawal': user_balance,
            'gas_cost': Decimal('0'),
            'platform_fee': Decimal('0'),
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
