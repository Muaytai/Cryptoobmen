#!/usr/bin/env python
"""
Скрипт для исправления проблемы с выводом Solana
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from transactions.models import Transfer
from crypto.models import UserWallet, Cryptocurrency

def fix_withdrawal():
    try:
        print("=== Диагностика проблемы с выводом Solana ===\n")
        
        # Находим вывод с ID 62
        withdrawal = Transfer.objects.get(id=62)
        print(f'Вывод ID: {withdrawal.id}')
        print(f'Текущий адрес получателя: {withdrawal.destination_address}')
        print(f'Сумма: {withdrawal.amount}')
        print(f'Статус: {withdrawal.transaction.status}')
        print(f'Hash транзакции: {withdrawal.transaction.tx_hash}')

        # Проверяем системный кошелек SOL
        sol_currency = Cryptocurrency.objects.get(symbol='SOL')
        system_wallet = UserWallet.objects.get(currency=sol_currency, is_system_wallet=True)
        print(f'Системный кошелек SOL: {system_wallet.deposit_address}')

        # Проверяем, совпадают ли адреса
        if withdrawal.destination_address == system_wallet.deposit_address:
            print("\n❌ ПРОБЛЕМА НАЙДЕНА: Адрес получателя совпадает с системным кошельком!")
            print("Это означает, что средства отправлены на системный кошелек вместо пользователя.")
            
            # Попробуем найти правильный адрес пользователя
            user_wallet = UserWallet.objects.filter(
                user=withdrawal.transaction.user,
                currency=sol_currency,
                is_system_wallet=False
            ).first()
            
            if user_wallet:
                print(f"\nПользовательский кошелек SOL: {user_wallet.deposit_address}")
                print(f"Пользователь: {withdrawal.transaction.user.email}")
                
                # Спрашиваем, исправить ли адрес
                print(f"\n🔧 ИСПРАВЛЕНИЕ:")
                print(f"Нужно изменить destination_address с '{withdrawal.destination_address}' на '{user_wallet.deposit_address}'")
                
                # В реальном случае здесь нужно было бы исправить данные
                # withdrawal.destination_address = user_wallet.deposit_address
                # withdrawal.save()
                
            else:
                print("\n❌ Не удалось найти пользовательский кошелек SOL")
        else:
            print("\n✅ Адреса не совпадают - проблема в другом месте")
            
        # Проверяем последние выводы SOL
        print(f"\n=== Последние 5 выводов SOL ===")
        recent_withdrawals = Transfer.objects.filter(
            transaction__crypto=sol_currency,
            transaction__type='withdrawal'
        ).order_by('-id')[:5]
        
        for w in recent_withdrawals:
            is_system = w.destination_address == system_wallet.deposit_address
            status_icon = "❌" if is_system else "✅"
            print(f'{status_icon} ID: {w.id}, Адрес: {w.destination_address[:8]}..., Сумма: {w.amount}, Статус: {w.transaction.status}')
            
    except Exception as e:
        print(f'Ошибка: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    fix_withdrawal()
