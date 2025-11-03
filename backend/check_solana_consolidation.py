#!/usr/bin/env python
"""
Проверка консолидации Solana - куда уходят средства и почему системный кошелек не пополняется
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from transactions.models import Transaction
from crypto.models import UserWallet, Cryptocurrency, SystemWalletAddress
from crypto.blockchain.factory import get_blockchain_service
from decimal import Decimal

def check_solana_consolidation():
    print("=== ПРОВЕРКА КОНСОЛИДАЦИИ SOLANA ===\n")
    
    try:
        # Находим SOL валюту (может быть несколько)
        sol_currencies = Cryptocurrency.objects.filter(symbol='SOL')
        print(f"Найдено {sol_currencies.count()} валют SOL:")
        for i, curr in enumerate(sol_currencies):
            print(f"  {i+1}. {curr.symbol} (сеть: {curr.network}, активна: {curr.is_active})")
        
        # Используем активную SOL или первую найденную
        sol_currency = sol_currencies.filter(is_active=True).first() or sol_currencies.first()
        print(f"\nИспользуем: {sol_currency.symbol} (сеть: {sol_currency.network})")
        
        # Проверяем системный кошелек через разные модели
        print(f"\n🔍 СИСТЕМНЫЕ КОШЕЛЬКИ SOL:")
        
        # 1. Через SystemWalletAddress
        try:
            system_wallet_addr = SystemWalletAddress.objects.get(currency=sol_currency)
            print(f"SystemWalletAddress: {system_wallet_addr.address}")
        except SystemWalletAddress.DoesNotExist:
            print("SystemWalletAddress: НЕ НАЙДЕН")
        
        # 2. Через UserWallet (старый способ)
        try:
            system_wallet = UserWallet.objects.get(currency=sol_currency, is_system_wallet=True, is_active=True)
            print(f"UserWallet (системный): {system_wallet.deposit_address}")
            print(f"Баланс в БД: {system_wallet.balance} SOL")
            print(f"Приватный ключ: {'ЕСТЬ' if system_wallet.encrypted_private_key else 'НЕТ'}")
        except UserWallet.DoesNotExist:
            print("UserWallet (системный): НЕ НАЙДЕН")
        
        # 3. Получаем адрес системного кошелька через функцию
        try:
            from crypto.tasks_consolidation import get_system_wallet_address
            system_addr = get_system_wallet_address(sol_currency)
            print(f"get_system_wallet_address(): {system_addr}")
        except Exception as e:
            print(f"get_system_wallet_address(): ОШИБКА - {e}")
        
        # Проверяем баланс системного кошелька в блокчейне
        print(f"\n💰 БАЛАНС СИСТЕМНОГО КОШЕЛЬКА В БЛОКЧЕЙНЕ:")
        try:
            service = get_blockchain_service(sol_currency.network)
            blockchain_balance = service.get_balance(system_addr)
            print(f"Баланс в блокчейне: {blockchain_balance} SOL")
        except Exception as e:
            print(f"Ошибка получения баланса: {e}")
        
        # Проверяем последние транзакции консолидации
        print(f"\n📊 ПОСЛЕДНИЕ 10 ТРАНЗАКЦИЙ КОНСОЛИДАЦИИ SOL:")
        consolidation_txs = Transaction.objects.filter(
            crypto=sol_currency,
            type='consolidation'
        ).order_by('-id')[:10]
        
        for tx in consolidation_txs:
            print(f"ID: {tx.id} | Статус: {tx.status} | Сумма: {tx.amount} SOL")
            print(f"  Hash: {tx.tx_hash}")
            print(f"  Пользователь: {tx.user.email if tx.user else 'N/A'}")
            print(f"  Создано: {tx.timestamp}")
            print()
        
        # Проверяем пользовательские кошельки с балансом
        print(f"\n👥 ПОЛЬЗОВАТЕЛЬСКИЕ КОШЕЛЬКИ SOL С БАЛАНСОМ:")
        user_wallets = UserWallet.objects.filter(
            currency=sol_currency,
            is_system_wallet=False,
            balance__gt=0
        ).order_by('-balance')[:5]
        
        for wallet in user_wallets:
            print(f"Пользователь: {wallet.user.email}")
            print(f"Адрес: {wallet.deposit_address}")
            print(f"Баланс в БД: {wallet.balance} SOL")
            print(f"Приватный ключ: {'ЕСТЬ' if wallet.encrypted_private_key else 'НЕТ'}")
            print()
        
        # Проверяем, есть ли активные задачи консолидации
        print(f"\n⚙️ АКТИВНЫЕ ЗАДАЧИ КОНСОЛИДАЦИИ:")
        try:
            from celery import current_app
            inspect = current_app.control.inspect()
            active_tasks = inspect.active()
            if active_tasks:
                for worker, tasks in active_tasks.items():
                    consolidation_tasks = [t for t in tasks if 'consolidat' in t['name'].lower()]
                    if consolidation_tasks:
                        print(f"Worker {worker}:")
                        for task in consolidation_tasks:
                            print(f"  - {task['name']} (ID: {task['id']})")
            else:
                print("Нет активных задач")
        except Exception as e:
            print(f"Ошибка проверки задач: {e}")
        
        # Проверяем настройки консолидации
        print(f"\n🔧 НАСТРОЙКИ КОНСОЛИДАЦИИ:")
        try:
            from crypto.tasks_consolidation import get_min_consolidation_amount, get_gas_reserve
            min_amount = get_min_consolidation_amount(sol_currency)
            gas_reserve = get_gas_reserve(sol_currency)
            print(f"Минимальная сумма для консолидации: {min_amount} SOL")
            print(f"Резерв газа: {gas_reserve} SOL")
        except Exception as e:
            print(f"Ошибка получения настроек: {e}")
            
    except Exception as e:
        print(f"Общая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_solana_consolidation()
