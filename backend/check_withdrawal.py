#!/usr/bin/env python
"""
Скрипт для проверки данных вывода Solana
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from transactions.models import Transfer
from crypto.models import UserWallet, Cryptocurrency

def check_withdrawal():
    try:
        # Находим вывод с ID 62
        withdrawal = Transfer.objects.get(id=62)
        print(f'Вывод ID: {withdrawal.id}')
        print(f'Адрес получателя: {withdrawal.destination_address}')
        print(f'Сумма: {withdrawal.amount}')
        print(f'Статус: {withdrawal.transaction.status}')
        print(f'Валюта: {withdrawal.transaction.crypto.symbol}')
        print(f'Hash транзакции: {withdrawal.transaction.tx_hash}')

        # Проверяем системный кошелек SOL
        sol_currency = Cryptocurrency.objects.get(symbol='SOL')
        system_wallet = UserWallet.objects.get(currency=sol_currency, is_system_wallet=True)
        print(f'Системный кошелек SOL: {system_wallet.deposit_address}')

        # Сравниваем адреса
        print(f'Адреса совпадают: {withdrawal.destination_address == system_wallet.deposit_address}')
        
        # Проверяем все недавние выводы SOL
        print('\n=== Последние 5 выводов SOL ===')
        recent_withdrawals = Transfer.objects.filter(
            transaction__crypto=sol_currency,
            transaction__type='withdrawal'
        ).order_by('-id')[:5]
        
        for w in recent_withdrawals:
            print(f'ID: {w.id}, Адрес: {w.destination_address}, Сумма: {w.amount}, Статус: {w.transaction.status}')
            
    except Exception as e:
        print(f'Ошибка: {e}')

if __name__ == '__main__':
    check_withdrawal()
