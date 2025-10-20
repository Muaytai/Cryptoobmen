#!/usr/bin/env python
"""
Скрипт для исправления неправильных адресов получателей в выводах
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from transactions.models import Transfer, Withdrawal
from crypto.models import UserWallet, Cryptocurrency

def fix_withdrawal_addresses():
    print("=== ИСПРАВЛЕНИЕ АДРЕСОВ ПОЛУЧАТЕЛЕЙ В ВЫВОДАХ ===\n")
    
    # Находим валюты
    sol_currency = Cryptocurrency.objects.get(symbol='SOL')
    pol_currency = Cryptocurrency.objects.get(symbol='POL')
    
    # Находим системные кошельки
    sol_system = UserWallet.objects.get(currency=sol_currency, is_system_wallet=True)
    pol_system = UserWallet.objects.get(currency=pol_currency, is_system_wallet=True)
    
    print(f"Системный кошелек SOL: {sol_system.deposit_address}")
    print(f"Системный кошелек POL: {pol_system.deposit_address}")
    
    # Исправляем выводы SOL
    print(f"\n🔧 ИСПРАВЛЕНИЕ ВЫВОДОВ SOL:")
    sol_problematic = Withdrawal.objects.filter(
        transaction__crypto=sol_currency,
        destination_address=sol_system.deposit_address,
        transaction__type='withdrawal'
    )
    
    fixed_sol = 0
    for withdrawal in sol_problematic:
        # Находим пользовательский кошелек SOL
        user_wallet = UserWallet.objects.filter(
            user=withdrawal.user,
            currency=sol_currency,
            is_system_wallet=False
        ).first()
        
        if user_wallet:
            old_address = withdrawal.destination_address
            withdrawal.destination_address = user_wallet.deposit_address
            withdrawal.save()
            
            print(f"✅ Вывод ID {withdrawal.id}:")
            print(f"   Старый адрес: {old_address}")
            print(f"   Новый адрес:  {withdrawal.destination_address}")
            print(f"   Пользователь: {withdrawal.user.email}")
            print(f"   Сумма: {withdrawal.transaction.amount} SOL")
            print()
            fixed_sol += 1
        else:
            print(f"❌ Вывод ID {withdrawal.id}: не найден пользовательский кошелек SOL")
    
    # Исправляем выводы POL
    print(f"🔧 ИСПРАВЛЕНИЕ ВЫВОДОВ POL:")
    pol_problematic = Withdrawal.objects.filter(
        transaction__crypto=pol_currency,
        destination_address=pol_system.deposit_address,
        transaction__type='withdrawal'
    )
    
    fixed_pol = 0
    for withdrawal in pol_problematic:
        # Находим пользовательский кошелек POL
        user_wallet = UserWallet.objects.filter(
            user=withdrawal.user,
            currency=pol_currency,
            is_system_wallet=False
        ).first()
        
        if user_wallet:
            old_address = withdrawal.destination_address
            withdrawal.destination_address = user_wallet.deposit_address
            withdrawal.save()
            
            print(f"✅ Вывод ID {withdrawal.id}:")
            print(f"   Старый адрес: {old_address}")
            print(f"   Новый адрес:  {withdrawal.destination_address}")
            print(f"   Пользователь: {withdrawal.user.email}")
            print(f"   Сумма: {withdrawal.transaction.amount} POL")
            print()
            fixed_pol += 1
        else:
            print(f"❌ Вывод ID {withdrawal.id}: не найден пользовательский кошелек POL")
    
    print(f"📊 ИТОГИ:")
    print(f"Исправлено выводов SOL: {fixed_sol}")
    print(f"Исправлено выводов POL: {fixed_pol}")
    
    if fixed_sol > 0 or fixed_pol > 0:
        print(f"\n✅ Исправления применены! Теперь можно перезапустить обработку выводов.")
        print(f"Команда для перезапуска: python manage.py shell -c \"from crypto.tasks import process_pending_withdrawals; process_pending_withdrawals()\"")
    else:
        print(f"\nℹ️ Не найдено проблемных выводов для исправления.")

if __name__ == '__main__':
    fix_withdrawal_addresses()
