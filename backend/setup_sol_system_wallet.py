#!/usr/bin/env python
"""
Настройка системного кошелька для SOL-Solana
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

def setup_sol_system_wallet():
    print("=== НАСТРОЙКА СИСТЕМНОГО КОШЕЛЬКА SOL-SOLANA ===\n")
    
    try:
        # Находим все валюты SOL
        sol_currencies = Cryptocurrency.objects.filter(symbol='SOL')
        print(f"Найдено {sol_currencies.count()} валют SOL:")
        
        for i, curr in enumerate(sol_currencies):
            print(f"  {i+1}. {curr.symbol} (сеть: {curr.network}, активна: {curr.is_active})")
        
        # Выбираем валюту SOL с сетью 'solana' или создаем её
        sol_currency = sol_currencies.filter(network='solana').first()
        
        if not sol_currency:
            print(f"\n🔧 Создаем валюту SOL с сетью 'solana'...")
            sol_currency = Cryptocurrency.objects.create(
                symbol='SOL',
                name='Solana',
                network='solana',
                decimals=9,
                is_active=True,
                min_exchange_amount=Decimal('0.01'),
                max_exchange_amount=Decimal('1000.0'),
                fee_percentage=Decimal('0.2'),
                requires_memo=False,
                currency_type='crypto'
            )
            print(f"✅ Создана валюта: {sol_currency}")
        else:
            print(f"\n✅ Используем существующую валюту: {sol_currency}")
        
        # Проверяем существующие системные кошельки
        print(f"\n🔍 ПРОВЕРКА СИСТЕМНЫХ КОШЕЛЬКОВ:")
        
        # 1. UserWallet (системный)
        system_wallet = UserWallet.objects.filter(
            currency=sol_currency,
            is_system_wallet=True,
            is_active=True
        ).first()
        
        if system_wallet:
            print(f"✅ UserWallet (системный) найден:")
            print(f"   ID: {system_wallet.id}")
            print(f"   Адрес: {system_wallet.deposit_address}")
            print(f"   Баланс: {system_wallet.balance} SOL")
            print(f"   Приватный ключ: {'ЕСТЬ' if system_wallet.encrypted_private_key else 'НЕТ'}")
        else:
            print(f"❌ UserWallet (системный) НЕ НАЙДЕН")
        
        # 2. SystemWalletAddress
        system_wallet_addr = SystemWalletAddress.objects.filter(
            currency=sol_currency
        ).first()
        
        if system_wallet_addr:
            print(f"✅ SystemWalletAddress найден:")
            print(f"   ID: {system_wallet_addr.id}")
            print(f"   Адрес: {system_wallet_addr.address}")
            print(f"   Приватный ключ: {'ЕСТЬ' if hasattr(system_wallet_addr, 'private_key') and system_wallet_addr.private_key else 'НЕТ'}")
        else:
            print(f"❌ SystemWalletAddress НЕ НАЙДЕН")
        
        # Если нет системного кошелька, создаем его
        if not system_wallet and not system_wallet_addr:
            print(f"\n🔧 СОЗДАНИЕ СИСТЕМНОГО КОШЕЛЬКА...")
            
            # Получаем блокчейн сервис
            service = get_blockchain_service(sol_currency.network)
            
            # Генерируем новый адрес
            new_address, private_key = service.create_new_address()
            
            print(f"✅ Сгенерирован новый адрес:")
            print(f"   Адрес: {new_address}")
            print(f"   Приватный ключ: {private_key[:20]}...")
            
            # Создаем UserWallet (системный)
            system_wallet = UserWallet.objects.create(
                user=None,  # Системный кошелек
                currency=sol_currency,
                deposit_address=new_address,
                encrypted_private_key=private_key,
                balance=Decimal('0'),
                available_balance=Decimal('0'),
                locked_balance=Decimal('0'),
                is_system_wallet=True,
                is_active=True
            )
            
            print(f"✅ UserWallet (системный) создан с ID: {system_wallet.id}")
            
            # Создаем SystemWalletAddress
            system_wallet_addr = SystemWalletAddress.objects.create(
                currency=sol_currency,
                address=new_address,
                private_key=private_key
            )
            
            print(f"✅ SystemWalletAddress создан с ID: {system_wallet_addr.id}")
        
        # Проверяем функцию get_system_wallet_address
        print(f"\n🧪 ТЕСТИРОВАНИЕ ФУНКЦИИ get_system_wallet_address():")
        try:
            from crypto.tasks_consolidation import get_system_wallet_address
            system_addr = get_system_wallet_address(sol_currency)
            print(f"✅ Функция работает: {system_addr}")
        except Exception as e:
            print(f"❌ Ошибка функции: {e}")
        
        # Проверяем баланс в блокчейне
        print(f"\n💰 ПРОВЕРКА БАЛАНСА В БЛОКЧЕЙНЕ:")
        try:
            service = get_blockchain_service(sol_currency.network)
            
            # Получаем адрес системного кошелька
            final_addr = system_wallet.deposit_address if system_wallet else system_wallet_addr.address
            blockchain_balance = service.get_balance(final_addr)
            
            print(f"Адрес системного кошелька: {final_addr}")
            print(f"Баланс в блокчейне: {blockchain_balance} SOL")
            
            if blockchain_balance < Decimal('0.01'):
                print(f"⚠️ РЕКОМЕНДАЦИЯ: Пополните системный кошелек SOL")
                print(f"   Отправьте SOL на адрес: {final_addr}")
                print(f"   Рекомендуемая сумма: 0.1-1.0 SOL")
            else:
                print(f"✅ Баланс достаточный для работы")
                
        except Exception as e:
            print(f"Ошибка проверки баланса: {e}")
        
        # Проверяем настройки консолидации
        print(f"\n⚙️ НАСТРОЙКИ КОНСОЛИДАЦИИ:")
        try:
            from crypto.tasks_consolidation import get_min_consolidation_amount, get_gas_reserve
            min_amount = get_min_consolidation_amount(sol_currency)
            gas_reserve = get_gas_reserve(sol_currency)
            print(f"Минимальная сумма для консолидации: {min_amount} SOL")
            print(f"Резерв газа: {gas_reserve} SOL")
        except Exception as e:
            print(f"Ошибка получения настроек: {e}")
        
        print(f"\n🎉 НАСТРОЙКА ЗАВЕРШЕНА!")
        print(f"Системный кошелек SOL-Solana готов к работе.")
        
    except Exception as e:
        print(f"Ошибка настройки: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    setup_sol_system_wallet()

