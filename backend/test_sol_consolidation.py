#!/usr/bin/env python
"""
Тестирование консолидации SOL-Solana
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from crypto.models import UserWallet, Cryptocurrency
from crypto.blockchain.factory import get_blockchain_service
from crypto.tasks_consolidation import get_system_wallet_address
from decimal import Decimal

def test_sol_consolidation():
    print("=== ТЕСТИРОВАНИЕ КОНСОЛИДАЦИИ SOL-SOLANA ===\n")
    
    try:
        # Находим валюту SOL с сетью 'solana'
        sol_currency = Cryptocurrency.objects.filter(symbol='SOL', network='solana').first()
        if not sol_currency:
            print("❌ Валюта SOL-Solana не найдена!")
            return
        
        print(f"Валюта: {sol_currency.symbol} (сеть: {sol_currency.network})")
        
        # Проверяем системный кошелек
        try:
            system_addr = get_system_wallet_address(sol_currency)
            print(f"✅ Системный адрес: {system_addr}")
        except Exception as e:
            print(f"❌ Ошибка получения системного адреса: {e}")
            return
        
        # Проверяем системный кошелек в БД
        system_wallet = UserWallet.objects.filter(
            currency=sol_currency,
            is_system_wallet=True,
            is_active=True
        ).first()
        
        if system_wallet:
            print(f"✅ Системный кошелек в БД:")
            print(f"   Адрес: {system_wallet.deposit_address}")
            print(f"   Баланс: {system_wallet.balance} SOL")
            print(f"   Приватный ключ: {'ЕСТЬ' if system_wallet.encrypted_private_key else 'НЕТ'}")
        else:
            print(f"❌ Системный кошелек в БД не найден!")
            return
        
        # Проверяем баланс в блокчейне
        service = get_blockchain_service(sol_currency.network)
        blockchain_balance = service.get_balance(system_addr)
        print(f"✅ Баланс в блокчейне: {blockchain_balance} SOL")
        
        # Проверяем пользовательские кошельки с балансом
        user_wallets = UserWallet.objects.filter(
            currency=sol_currency,
            is_system_wallet=False,
            balance__gt=0
        ).order_by('-balance')[:5]
        
        print(f"\n👥 ПОЛЬЗОВАТЕЛЬСКИЕ КОШЕЛЬКИ SOL С БАЛАНСОМ:")
        if user_wallets.exists():
            print(f"Найдено {user_wallets.count()} кошельков с балансом:")
            for wallet in user_wallets:
                print(f"  - {wallet.user.email}: {wallet.balance} SOL")
                print(f"    Адрес: {wallet.deposit_address}")
                print(f"    Приватный ключ: {'ЕСТЬ' if wallet.encrypted_private_key else 'НЕТ'}")
        else:
            print("Нет пользовательских кошельков с балансом")
        
        # Тестируем функцию консолидации
        print(f"\n🧪 ТЕСТИРОВАНИЕ ФУНКЦИИ КОНСОЛИДАЦИИ:")
        
        if user_wallets.exists():
            test_wallet = user_wallets.first()
            print(f"Тестируем с кошельком: {test_wallet.deposit_address}")
            
            # Проверяем баланс в блокчейне
            try:
                blockchain_balance = service.get_balance(test_wallet.deposit_address)
                print(f"Баланс в блокчейне: {blockchain_balance} SOL")
                
                # Проверяем настройки консолидации
                from crypto.tasks_consolidation import get_min_consolidation_amount, get_gas_reserve
                min_amount = get_min_consolidation_amount(sol_currency)
                gas_reserve = get_gas_reserve(sol_currency)
                
                print(f"Минимальная сумма для консолидации: {min_amount} SOL")
                print(f"Резерв газа: {gas_reserve} SOL")
                
                if blockchain_balance >= min_amount:
                    print(f"✅ Кошелек подходит для консолидации")
                    print(f"Будет отправлено: {blockchain_balance - gas_reserve} SOL")
                    print(f"На адрес: {system_addr}")
                else:
                    print(f"⚠️ Баланс меньше минимального порога")
                    
            except Exception as e:
                print(f"Ошибка проверки баланса: {e}")
        else:
            print("Нет кошельков для тестирования")
        
        # Проверяем последние транзакции консолидации
        print(f"\n📊 ПОСЛЕДНИЕ ТРАНЗАКЦИИ КОНСОЛИДАЦИИ:")
        from transactions.models import Transaction
        consolidation_txs = Transaction.objects.filter(
            crypto=sol_currency,
            type='consolidation'
        ).order_by('-id')[:5]
        
        if consolidation_txs.exists():
            print(f"Найдено {consolidation_txs.count()} транзакций:")
            for tx in consolidation_txs:
                print(f"  - ID: {tx.id}, Статус: {tx.status}, Сумма: {tx.amount} SOL")
                print(f"    Hash: {tx.tx_hash}")
                print(f"    Пользователь: {tx.user.email if tx.user else 'N/A'}")
        else:
            print("Нет транзакций консолидации")
        
        print(f"\n🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
        print(f"Системный кошелек SOL-Solana готов к консолидации.")
        
    except Exception as e:
        print(f"Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_sol_consolidation()

