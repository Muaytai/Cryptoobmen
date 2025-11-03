#!/usr/bin/env python
"""
Сравнение логики вывода средств Solana и Polygon
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from transactions.models import Transfer, Withdrawal
from crypto.models import UserWallet, Cryptocurrency

def compare_withdrawals():
    print("=== СРАВНЕНИЕ ВЫВОДОВ SOLANA И POLYGON ===\n")
    
    # Находим валюты
    sol_currency = Cryptocurrency.objects.get(symbol='SOL')
    pol_currency = Cryptocurrency.objects.get(symbol='POL')
    
    # Находим системные кошельки
    sol_system = UserWallet.objects.get(currency=sol_currency, is_system_wallet=True)
    pol_system = UserWallet.objects.get(currency=pol_currency, is_system_wallet=True)
    
    print("🔍 СИСТЕМНЫЕ КОШЕЛЬКИ:")
    print(f"SOL системный: {sol_system.deposit_address}")
    print(f"POL системный: {pol_system.deposit_address}")
    
    # Находим последние выводы SOL
    print(f"\n📊 ПОСЛЕДНИЕ 5 ВЫВОДОВ SOL:")
    sol_withdrawals = Withdrawal.objects.filter(
        transaction__crypto=sol_currency,
        transaction__type='withdrawal'
    ).order_by('-id')[:5]
    
    for w in sol_withdrawals:
        is_system = w.destination_address == sol_system.deposit_address
        status_icon = "❌ СИСТЕМНЫЙ" if is_system else "✅ ПОЛЬЗОВАТЕЛЬСКИЙ"
        print(f"ID: {w.id} | {status_icon}")
        print(f"  Адрес: {w.destination_address}")
        print(f"  Сумма: {w.transaction.amount} SOL")
        print(f"  Статус: {w.transaction.status}")
        print(f"  Пользователь: {w.user.email}")
        print()
    
    # Находим последние выводы POL
    print(f"📊 ПОСЛЕДНИЕ 5 ВЫВОДОВ POL:")
    pol_withdrawals = Withdrawal.objects.filter(
        transaction__crypto=pol_currency,
        transaction__type='withdrawal'
    ).order_by('-id')[:5]
    
    for w in pol_withdrawals:
        is_system = w.destination_address == pol_system.deposit_address
        status_icon = "❌ СИСТЕМНЫЙ" if is_system else "✅ ПОЛЬЗОВАТЕЛЬСКИЙ"
        print(f"ID: {w.id} | {status_icon}")
        print(f"  Адрес: {w.destination_address}")
        print(f"  Сумма: {w.transaction.amount} POL")
        print(f"  Статус: {w.transaction.status}")
        print(f"  Пользователь: {w.user.email}")
        print()
    
    # Анализируем проблему
    print("🔍 АНАЛИЗ ПРОБЛЕМЫ:")
    problematic_sol = sol_withdrawals.filter(destination_address=sol_system.deposit_address)
    problematic_pol = pol_withdrawals.filter(destination_address=pol_system.deposit_address)
    
    print(f"Проблемных выводов SOL: {problematic_sol.count()}")
    print(f"Проблемных выводов POL: {problematic_pol.count()}")
    
    if problematic_sol.exists():
        print("\n❌ ПРОБЛЕМА НАЙДЕНА В SOL:")
        for w in problematic_sol:
            print(f"  Вывод ID {w.id}: адрес получателя = системный кошелек")
            print(f"  Пользователь: {w.user.email}")
            print(f"  Сумма: {w.transaction.amount} SOL")
    
    if problematic_pol.exists():
        print("\n❌ ПРОБЛЕМА НАЙДЕНА В POL:")
        for w in problematic_pol:
            print(f"  Вывод ID {w.id}: адрес получателя = системный кошелек")
            print(f"  Пользователь: {w.user.email}")
            print(f"  Сумма: {w.transaction.amount} POL")
    
    # Проверяем логику создания выводов
    print(f"\n🔧 ЛОГИКА СОЗДАНИЯ ВЫВОДОВ:")
    print("1. WithdrawalService.create_withdrawal_request() создает Withdrawal")
    print("2. destination_address сохраняется из параметра API")
    print("3. process_withdrawal() использует withdrawal.destination_address")
    print("4. Проблема: destination_address = системный кошелек вместо пользовательского")
    
    print(f"\n💡 ВОЗМОЖНЫЕ ПРИЧИНЫ:")
    print("1. Ошибка в API запросе (фронтенд передает неправильный адрес)")
    print("2. Ошибка в валидации адреса")
    print("3. Проблема в логике определения кошелька пользователя")
    print("4. Ошибка в базе данных (дублирование адресов)")

if __name__ == '__main__':
    compare_withdrawals()
