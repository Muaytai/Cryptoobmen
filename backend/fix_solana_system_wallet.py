#!/usr/bin/env python
"""
Исправление проблемы с системным кошельком Solana
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from crypto.models import UserWallet, Cryptocurrency, SystemWalletAddress
from crypto.blockchain.factory import get_blockchain_service
from decimal import Decimal

def fix_solana_system_wallet():
    print("=== ИСПРАВЛЕНИЕ СИСТЕМНОГО КОШЕЛЬКА SOLANA ===\n")
    
    try:
        # Находим SOL валюту
        sol_currencies = Cryptocurrency.objects.filter(symbol='SOL')
        print(f"Найдено {sol_currencies.count()} валют SOL:")
        for i, curr in enumerate(sol_currencies):
            print(f"  {i+1}. {curr.symbol} (сеть: {curr.network}, активна: {curr.is_active})")
        
        # Используем активную SOL или первую найденную
        sol_currency = sol_currencies.filter(is_active=True).first() or sol_currencies.first()
        print(f"\nРаботаем с: {sol_currency.symbol} (сеть: {sol_currency.network})")
        
        # Проверяем существующие системные кошельки
        print(f"\n🔍 ПРОВЕРКА СУЩЕСТВУЮЩИХ СИСТЕМНЫХ КОШЕЛЬКОВ:")
        
        # 1. SystemWalletAddress
        try:
            system_wallet_addr = SystemWalletAddress.objects.get(currency=sol_currency)
            print(f"✅ SystemWalletAddress найден: {system_wallet_addr.address}")
        except SystemWalletAddress.DoesNotExist:
            print("❌ SystemWalletAddress НЕ НАЙДЕН")
        
        # 2. UserWallet (системный)
        try:
            system_wallet = UserWallet.objects.get(currency=sol_currency, is_system_wallet=True, is_active=True)
            print(f"✅ UserWallet (системный) найден: {system_wallet.deposit_address}")
            print(f"   Баланс в БД: {system_wallet.balance} SOL")
        except UserWallet.DoesNotExist:
            print("❌ UserWallet (системный) НЕ НАЙДЕН")
        
        # Проверяем, есть ли хотя бы один системный кошелек
        has_system_wallet = False
        
        # Проверяем SystemWalletAddress
        try:
            SystemWalletAddress.objects.get(currency=sol_currency)
            has_system_wallet = True
            print(f"\n✅ SystemWalletAddress существует")
        except SystemWalletAddress.DoesNotExist:
            pass
        
        # Проверяем UserWallet системный
        try:
            UserWallet.objects.get(currency=sol_currency, is_system_wallet=True, is_active=True)
            has_system_wallet = True
            print(f"✅ UserWallet системный существует")
        except UserWallet.DoesNotExist:
            pass
        
        if not has_system_wallet:
            print(f"\n🚨 ПРОБЛЕМА: Нет системного кошелька для SOL!")
            print(f"Это объясняет, почему крипта не попадает на системный кошелек после консолидации.")
            
            # Показываем, как создать системный кошелек
            print(f"\n🔧 РЕШЕНИЕ:")
            print(f"1. Создать системный кошелек через админку или команду")
            print(f"2. Установить приватный ключ")
            print(f"3. Пополнить кошелек SOL для покрытия комиссий")
            
            # Проверяем, есть ли команда для создания системного кошелька
            print(f"\n📋 КОМАНДЫ ДЛЯ ИСПРАВЛЕНИЯ:")
            print(f"python manage.py fix_solana_issues --private-key=\"ВАШ_ПРИВАТНЫЙ_КЛЮЧ\"")
            print(f"python manage.py check_solana_system_wallet")
            
        else:
            print(f"\n✅ Системный кошелек существует")
            
            # Проверяем баланс системного кошелька
            print(f"\n💰 ПРОВЕРКА БАЛАНСА СИСТЕМНОГО КОШЕЛЬКА:")
            try:
                service = get_blockchain_service(sol_currency.network)
                
                # Получаем адрес системного кошелька
                from crypto.tasks_consolidation import get_system_wallet_address
                system_addr = get_system_wallet_address(sol_currency)
                
                # Проверяем баланс в блокчейне
                blockchain_balance = service.get_balance(system_addr)
                print(f"Адрес системного кошелька: {system_addr}")
                print(f"Баланс в блокчейне: {blockchain_balance} SOL")
                
                if blockchain_balance < Decimal('0.01'):
                    print(f"⚠️ НИЗКИЙ БАЛАНС! Рекомендуется пополнить системный кошелек")
                else:
                    print(f"✅ Баланс достаточный для работы")
                    
            except Exception as e:
                print(f"Ошибка проверки баланса: {e}")
        
        # Проверяем пользовательские кошельки с балансом
        print(f"\n👥 ПОЛЬЗОВАТЕЛЬСКИЕ КОШЕЛЬКИ SOL С БАЛАНСОМ:")
        user_wallets = UserWallet.objects.filter(
            currency=sol_currency,
            is_system_wallet=False,
            balance__gt=0
        ).order_by('-balance')[:5]
        
        if user_wallets.exists():
            print(f"Найдено {user_wallets.count()} пользовательских кошельков с балансом:")
            for wallet in user_wallets:
                print(f"  - {wallet.user.email}: {wallet.balance} SOL")
                print(f"    Адрес: {wallet.deposit_address}")
                print(f"    Приватный ключ: {'ЕСТЬ' if wallet.encrypted_private_key else 'НЕТ'}")
        else:
            print("Нет пользовательских кошельков с балансом")
        
        # Проверяем последние транзакции консолидации
        print(f"\n📊 ПОСЛЕДНИЕ ТРАНЗАКЦИИ КОНСОЛИДАЦИИ:")
        from transactions.models import Transaction
        consolidation_txs = Transaction.objects.filter(
            crypto=sol_currency,
            type='consolidation'
        ).order_by('-id')[:5]
        
        if consolidation_txs.exists():
            print(f"Найдено {consolidation_txs.count()} транзакций консолидации:")
            for tx in consolidation_txs:
                print(f"  - ID: {tx.id}, Статус: {tx.status}, Сумма: {tx.amount} SOL")
                print(f"    Hash: {tx.tx_hash}")
        else:
            print("Нет транзакций консолидации")
            
    except Exception as e:
        print(f"Общая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    fix_solana_system_wallet()

