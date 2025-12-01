#!/usr/bin/env python
"""
Скрипт для ручной консолидации средств с пользовательских кошельков на системный кошелек.

Использование:
    python manual_consolidate_wallets.py

Скрипт пробегает по всем пользовательским кошелькам в базе данных,
проверяет баланс на блокчейне и консолидирует средства на системный кошелек,
создавая соответствующие записи в БД.
"""

import os
import sys
import django
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
import time

# Настройка Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from crypto.models import Cryptocurrency, UserWallet, GeneratedWallet
from crypto.blockchain.factory import get_blockchain_service
from crypto.tasks_consolidation import (
    get_gas_reserve,
    get_min_consolidation_amount,
    get_system_wallet_address
)
from transactions.models import Transaction


def retry_on_rpc_error(max_retries=3, delay=2, backoff=2):
    """Декоратор для повторных попыток при RPC ошибках"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        raise
                    wait_time = delay * (backoff ** (attempt - 1))
                    print(f"⚠️  Попытка {attempt}/{max_retries} не удалась: {e}. Повтор через {wait_time}с...")
                    time.sleep(wait_time)
            return None
        return wrapper
    return decorator


def consolidate_wallet(generated_wallet, currency, blockchain_service, system_wallet_address):
    """Консолидирует средства с одного кошелька из GeneratedWallet"""
    try:
        address = generated_wallet.address
        user_info = f"пользователя {generated_wallet.user.id}" if generated_wallet.user else "системный"
        print(f"👤 Обработка кошелька {user_info}: {address[:10]}...")
        
        # Получаем приватный ключ из GeneratedWallet
        private_key_input = generated_wallet.encrypted_private_key
        if not private_key_input:
            print(f"⚠️  Приватный ключ не найден для кошелька {address[:10]}..., пропускаем")
            return False
        
        # Получаем баланс на блокчейне
        contract_address = currency.contract_address if currency.network and currency.network.upper() == 'TRC20' else None
        if contract_address:
            blockchain_balance = blockchain_service.get_balance(address, contract_address=contract_address)
        else:
            blockchain_balance = blockchain_service.get_balance(address)
        
        print(f"💰 Баланс на блокчейне: {blockchain_balance} {currency.symbol}")
        
        # Проверяем минимальный порог
        min_consolidation_amount = get_min_consolidation_amount(currency)
        if blockchain_balance < min_consolidation_amount:
            print(f"⚠️  Баланс {blockchain_balance} {currency.symbol} слишком мал для консолидации (мин: {min_consolidation_amount})")
            return False
        
                    # Рассчитываем максимальную сумму к переводу
        gas_cost = Decimal('0')
        
        if hasattr(blockchain_service, 'get_max_sendable_amount'):
            amount_to_send = blockchain_service.get_max_sendable_amount(
                address,
                system_wallet_address
            )
            gas_cost = blockchain_balance - amount_to_send
            print(f"💸 Максимальная сумма к отправке: {amount_to_send} {currency.symbol}")
            print(f"⛽ Стоимость газа: {gas_cost} {currency.symbol}")
        elif hasattr(blockchain_service, 'estimate_gas_fee'):
            gas_info = blockchain_service.estimate_gas_fee(
                to_address=system_wallet_address,
                amount=blockchain_balance,
                contract_address=getattr(currency, 'contract_address', None)
            )
            gas_cost = gas_info.get('gas_fee_eth', Decimal('0'))
            amount_to_send = blockchain_balance - gas_cost
            print(f"⛽ Стоимость газа (из estimate_gas_fee): {gas_cost} {currency.symbol}")
            print(f"💸 Сумма к отправке: {amount_to_send} {currency.symbol}")
        elif currency.symbol == 'BTC':
            amount_to_send = Decimal('0')  # 0 означает sweep всех средств
            gas_cost = get_gas_reserve(currency)
            print(f"💸 Bitcoin sweep mode: отправим все средства")
            print(f"⛽ Оценочная стоимость газа для BTC: {gas_cost} {currency.symbol}")
        else:
            from crypto.gas_calculation import calculate_estimated_gas_cost
            gas_cost = calculate_estimated_gas_cost(
                currency=currency,
                deposit_amount=blockchain_balance,
                user_address=address
            )
            amount_to_send = blockchain_balance - gas_cost
            print(f"⛽ Стоимость газа (оценка): {gas_cost} {currency.symbol}")
            print(f"💸 Сумма к отправке: {amount_to_send} {currency.symbol}")
        
        if amount_to_send <= 0 and currency.symbol != 'BTC':
            print(f"⚠️  Сумма к отправке {amount_to_send} {currency.symbol} равна нулю или отрицательна")
            return False
        
        # ⚠️ ВАЖНО: Для TRC-20 токенов проверяем наличие TRX для оплаты газа
        contract_address_for_send = currency.contract_address if currency.network and currency.network.upper() == 'TRC20' else None
        
        if currency.network and currency.network.upper() == 'TRC20':
            # Получаем баланс TRX на адресе
            trx_balance = blockchain_service.get_balance(address)
            min_trx_for_gas = Decimal('3')  # Минимум TRX для оплаты газа
            
            print(f"💎 Баланс TRX на адресе: {trx_balance} TRX (минимум требуется: {min_trx_for_gas} TRX)")
            
            if trx_balance < min_trx_for_gas:
                print(f"⚠️  Недостаточно TRX ({trx_balance} TRX) для оплаты газа. Нужно отправить TRX с системного кошелька.")
                try:
                    from crypto.models import SystemWalletAddress
                    trx_currency = Cryptocurrency.objects.get(symbol='TRX', network='TRC20')
                    system_trx_wallet = SystemWalletAddress.objects.get(currency=trx_currency)
                    
                    system_trx_balance = blockchain_service.get_balance(system_trx_wallet.address)
                    print(f"💎 Баланс системного TRX кошелька: {system_trx_balance} TRX")
                    
                    trx_amount_needed = min_trx_for_gas - trx_balance
                    trx_amount_to_send = trx_amount_needed + Decimal('1')  # Запас
                    trx_transaction_fee = Decimal('0.1')
                    total_trx_needed = trx_amount_to_send + trx_transaction_fee
                    
                    if system_trx_balance < total_trx_needed:
                        print(f"❌ Недостаточно TRX на системном кошельке! Баланс: {system_trx_balance} TRX, нужно: {total_trx_needed} TRX")
                        return False
                    
                    # Отправляем TRX для оплаты газа
                    trx_service = get_blockchain_service('TRC20')
                    print(f"💸 Отправка {trx_amount_to_send} TRX с системного кошелька для оплаты газа...")
                    
                    system_trx_private_key = system_trx_wallet.private_key
                    
                    @retry_on_rpc_error(max_retries=3, delay=2, backoff=2)
                    def send_trx_for_gas():
                        return trx_service.send_transaction(
                            private_key=system_trx_private_key,
                            to_address=address,
                            amount=trx_amount_to_send,
                        )
                    
                    gas_tx_hash = send_trx_for_gas()
                    print(f"✅ TRX для газа отправлен успешно: {gas_tx_hash}")
                    
                    # Ждем подтверждения
                    print(f"⏳ Ожидание 10 секунд для подтверждения TRX транзакции...")
                    time.sleep(10)
                    
                    new_trx_balance = blockchain_service.get_balance(address)
                    print(f"💎 Новый баланс TRX после перевода: {new_trx_balance} TRX")
                    
                    if new_trx_balance < min_trx_for_gas:
                        print(f"⚠️  Баланс TRX все еще недостаточен. Ожидание еще 10 секунд...")
                        time.sleep(10)
                        new_trx_balance = blockchain_service.get_balance(address)
                        print(f"💎 Баланс TRX после дополнительного ожидания: {new_trx_balance} TRX")
                    
                except Exception as gas_error:
                    print(f"❌ Ошибка при отправке TRX для газа: {gas_error}")
                    return False
            else:
                print(f"✅ Достаточно TRX ({trx_balance} TRX) для оплаты газа")
        
        # Отправляем транзакцию консолидации
        print(f"🚀 Консолидация {amount_to_send} {currency.symbol} с {address} на системный кошелек")
        
        @retry_on_rpc_error(max_retries=3, delay=2, backoff=2)
        def send_consolidation_transaction():
            import inspect
            sig = inspect.signature(blockchain_service.send_transaction)
            params = list(sig.parameters.keys())
            
            user_id = generated_wallet.user.id if generated_wallet.user else 0
            if 'contract_address' in params and contract_address_for_send:
                return blockchain_service.send_transaction(
                    private_key=private_key_input,
                    to_address=system_wallet_address,
                    amount=amount_to_send,
                    memo=f"consolidation_{user_id}",
                    contract_address=contract_address_for_send
                )
            else:
                return blockchain_service.send_transaction(
                    private_key=private_key_input,
                    to_address=system_wallet_address,
                    amount=amount_to_send,
                    memo=f"consolidation_{user_id}"
                )
        
        tx_hash = send_consolidation_transaction()
        if not tx_hash:
            user_info = f"пользователя {generated_wallet.user.id}" if generated_wallet.user else "кошелька"
            print(f"⚠️  Не получен tx_hash для {user_info}, пропускаем")
            return False
        
        print(f"✅ Транзакция отправлена успешно: {tx_hash}")
        
        # Сохраняем транзакцию в БД (только если есть пользователь)
        if generated_wallet.user:
            # ⚠️ КРИТИЧЕСКИ ВАЖНО: Проверяем наличие депозита в БД перед созданием консолидации
            # Консолидация НЕ должна создаваться раньше депозита
            has_deposit = Transaction.objects.filter(
                user=generated_wallet.user,
                crypto=currency,
                type="deposit"
            ).exists()
            
            if not has_deposit:
                print(f"⚠️  ВНИМАНИЕ: Транзакция консолидации {tx_hash} отправлена, но НЕ сохранена в БД")
                print(f"⚠️  Причина: нет депозита в БД для пользователя {generated_wallet.user.id}")
                print(f"⚠️  Консолидация не может быть создана раньше депозита")
                print(f"⚠️  Средства консолидированы на блокчейне, но запись в БД не создана")
                # Возвращаем True, так как транзакция была успешно отправлена
                # Это позволяет скрипту продолжить обработку других кошельков
                return True
            
            consolidation_amount_to_save = amount_to_send if currency.symbol != 'BTC' else blockchain_balance
            
            with transaction.atomic():
                Transaction.objects.create(
                    user=generated_wallet.user,
                    crypto=currency,
                    amount=consolidation_amount_to_save,
                    fee=gas_cost,
                    tx_hash=tx_hash,
                    type="consolidation",
                    status="pending",
                    timestamp=timezone.now()
                )
            
            print(f"💾 Транзакция консолидации сохранена в БД: {tx_hash}")
            print(f"🎉 Успешно консолидировано {consolidation_amount_to_save} {currency.symbol} для пользователя {generated_wallet.user.id}")
        else:
            print(f"💾 Транзакция отправлена, но не сохранена в БД (системный кошелек без пользователя)")
            print(f"🎉 Успешно консолидировано {amount_to_send} {currency.symbol} с адреса {address}")
        
        return True
        
    except Exception as e:
        user_info = f"пользователя {generated_wallet.user.id}" if generated_wallet.user else "кошелька"
        print(f"❌ Ошибка при консолидации {currency.symbol} для {user_info}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Основная функция скрипта"""
    print("=" * 60)
    print("🚀 Запуск ручной консолидации средств")
    print(f"⏰ Время начала: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Получаем все активные валюты без MEMO
    currencies_no_memo = Cryptocurrency.objects.filter(
        is_active=True,
        requires_memo=False
    )
    
    print(f"📊 Найдено {currencies_no_memo.count()} валют без MEMO: {[c.symbol for c in currencies_no_memo]}")
    
    total_processed = 0
    
    for currency in currencies_no_memo:
        print("-" * 50)
        print(f"🔄 Обработка консолидации для {currency.symbol} ({currency.network})")
        
        try:
            # Получаем системный кошелек
            system_wallet = UserWallet.objects.get(
                user=None,
                currency=currency,
                is_system_wallet=True,
                is_active=True
            )
            
            if not system_wallet.encrypted_private_key:
                print(f"⚠️  Системный кошелек для {currency.symbol} не имеет приватного ключа, пропускаем")
                continue
            
            system_wallet_address = get_system_wallet_address(currency)
            print(f"🏦 Системный кошелек: {system_wallet_address}")
            
            # Получаем ВСЕ кошельки из GeneratedWallet для этой валюты
            # Фильтруем только пользовательские кошельки (не системные)
            all_generated_wallets = GeneratedWallet.objects.filter(
                currency=currency,
                wallet_type='user',
                is_active=True
            )
            
            print(f"👥 Найдено {all_generated_wallets.count()} кошельков в GeneratedWallet для {currency.symbol}")
            
            if all_generated_wallets.count() == 0:
                print(f"⏭️  Нет кошельков в GeneratedWallet для {currency.symbol}, пропускаем")
                continue
            
            # Создаем сервис блокчейна для проверки балансов
            blockchain_service = get_blockchain_service(currency.network or currency.symbol)
            print(f"🔗 Подключено к сервису блокчейна {currency.network}")
            
            # Получаем минимальный порог консолидации
            min_consolidation_amount = get_min_consolidation_amount(currency)
            print(f"💰 Минимальный порог консолидации: {min_consolidation_amount} {currency.symbol}")
            
            # Фильтруем только неиспользуемые кошельки (без pending депозитов)
            # Кошелек считается неиспользуемым, если:
            # 1. Нет pending депозитов
            # 2. Нет pending консолидаций
            # 3. Имеет баланс на блокчейне выше минимального порога
            unused_wallets = []
            contract_address = currency.contract_address if currency.network and currency.network.upper() == 'TRC20' else None
            
            for gen_wallet in all_generated_wallets:
                # Пропускаем кошельки без пользователя (они могут быть системными или тестовыми)
                if not gen_wallet.user:
                    continue
                
                # ⚠️ ВАЖНО: Проверяем баланс на блокчейне ПЕРЕД фильтрацией по транзакциям
                # Это позволяет не пропускать кошельки с балансом, но без записей в БД
                try:
                    if contract_address:
                        blockchain_balance = blockchain_service.get_balance(gen_wallet.address, contract_address=contract_address)
                    else:
                        blockchain_balance = blockchain_service.get_balance(gen_wallet.address)
                    
                    # Пропускаем кошельки с балансом ниже минимального порога
                    if blockchain_balance < min_consolidation_amount:
                        print(f"⏭️  Кошелек {gen_wallet.address[:10]}... имеет баланс {blockchain_balance} {currency.symbol} ниже порога {min_consolidation_amount}, пропускаем")
                        continue
                    
                    print(f"💰 Кошелек {gen_wallet.address[:10]}... имеет баланс {blockchain_balance} {currency.symbol} (выше порога)")
                except Exception as balance_error:
                    print(f"⚠️  Ошибка при проверке баланса для кошелька {gen_wallet.address[:10]}...: {balance_error}, пропускаем")
                    continue
                
                # Проверяем наличие pending депозитов
                has_pending = Transaction.objects.filter(
                    user=gen_wallet.user,
                    crypto=currency,
                    type="deposit",
                    status="pending"
                ).exists()
                
                if has_pending:
                    print(f"⏭️  Кошелек {gen_wallet.address[:10]}... имеет pending депозиты, пропускаем")
                    continue
                
                # Проверяем, есть ли pending консолидации для этого кошелька
                has_pending_consolidation = Transaction.objects.filter(
                    user=gen_wallet.user,
                    crypto=currency,
                    type="consolidation",
                    status="pending"
                ).exists()
                
                if has_pending_consolidation:
                    print(f"⏭️  Кошелек {gen_wallet.address[:10]}... имеет pending консолидацию, пропускаем")
                    continue
                
                # Все проверки пройдены, добавляем кошелек в список для обработки
                print(f"✅ Кошелек {gen_wallet.address[:10]}... добавлен в список для консолидации")
                unused_wallets.append(gen_wallet)
            
            print(f"📋 Найдено {len(unused_wallets)} неиспользуемых кошельков для {currency.symbol} с балансом выше порога (без pending депозитов и pending консолидаций)")
            
            if len(unused_wallets) == 0:
                print(f"⏭️  Нет неиспользуемых кошельков для {currency.symbol} с балансом выше порога, пропускаем")
                continue
            
            generated_wallets = unused_wallets
            
            currency_processed = 0
            for gen_wallet in generated_wallets:
                if consolidate_wallet(gen_wallet, currency, blockchain_service, system_wallet_address):
                    currency_processed += 1
                    total_processed += 1
                    # Небольшая пауза между транзакциями
                    time.sleep(1)
            
            print(f"📈 Итог по {currency.symbol}: обработано {currency_processed} транзакций")
            
        except UserWallet.DoesNotExist:
            print(f"⚠️  Системный кошелек для {currency.symbol} не найден, пропускаем")
            continue
        except Exception as e:
            print(f"❌ Ошибка при обработке валюты {currency.symbol}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("=" * 60)
    print(f"🏁 Процесс консолидации завершен")
    print(f"✅ Всего обработано: {total_processed} транзакций")
    print(f"⏰ Время окончания: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == '__main__':
    main()

