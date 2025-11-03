#!/usr/bin/env python
"""
Создание системного кошелька для Solana
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from crypto.models import UserWallet, Cryptocurrency
from crypto.blockchain.factory import get_blockchain_service
from decimal import Decimal

def create_sol_system_wallet():
    print("=== СОЗДАНИЕ СИСТЕМНОГО КОШЕЛЬКА SOL ===\n")
    
    try:
        # Находим SOL валюту
        sol_currency = Cryptocurrency.objects.filter(symbol='SOL').first()
        if not sol_currency:
            print("❌ Валюта SOL не найдена!")
            return
        
        print(f"Работаем с валютой: {sol_currency.symbol} (сеть: {sol_currency.network})")
        
        # Проверяем, есть ли уже системный кошелек
        existing_wallet = UserWallet.objects.filter(
            currency=sol_currency,
            is_system_wallet=True,
            is_active=True
        ).first()
        
        if existing_wallet:
            print(f"✅ Системный кошелек уже существует:")
            print(f"   Адрес: {existing_wallet.deposit_address}")
            print(f"   Баланс: {existing_wallet.balance} SOL")
            print(f"   Приватный ключ: {'ЕСТЬ' if existing_wallet.encrypted_private_key else 'НЕТ'}")
            return existing_wallet
        
        # Создаем новый системный кошелек
        print(f"🔧 Создаем новый системный кошелек...")
        
        # Получаем блокчейн сервис
        service = get_blockchain_service(sol_currency.network)
        
        # Генерируем новый адрес
        new_address, private_key = service.create_new_address()
        
        print(f"✅ Сгенерирован новый адрес:")
        print(f"   Адрес: {new_address}")
        print(f"   Приватный ключ: {private_key[:20]}...")
        
        # Создаем системный кошелек
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
        
        print(f"✅ Системный кошелек создан с ID: {system_wallet.id}")
        
        # Проверяем баланс в блокчейне
        try:
            blockchain_balance = service.get_balance(new_address)
            print(f"💰 Баланс в блокчейне: {blockchain_balance} SOL")
            
            if blockchain_balance < Decimal('0.1'):
                print(f"⚠️ РЕКОМЕНДАЦИЯ: Пополните системный кошелек SOL для покрытия комиссий")
                print(f"   Отправьте SOL на адрес: {new_address}")
            else:
                print(f"✅ Баланс достаточный для работы")
                
        except Exception as e:
            print(f"Ошибка проверки баланса: {e}")
        
        return system_wallet
        
    except Exception as e:
        print(f"Ошибка создания системного кошелька: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_sol_system_wallet()

