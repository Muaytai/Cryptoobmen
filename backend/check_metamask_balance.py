#!/usr/bin/env python
"""
Скрипт для проверки баланса адреса MetaMask в BNB Smart Chain Testnet
"""
import os
import sys
import django

# Добавляем путь к Django проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from crypto.blockchain.factory import get_blockchain_service
from decimal import Decimal

def check_balance(address):
    """Проверяет баланс BNB на указанном адресе"""
    try:
        service = get_blockchain_service('BEP20')
        balance = service.get_balance(address)
        return balance
    except Exception as e:
        print(f"Ошибка получения баланса: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python check_metamask_balance.py <address>")
        print("Пример: python check_metamask_balance.py 0xeA6BFd33720eCEBB96FB7FD1Bf5daCceF89")
        sys.exit(1)
    
    address = sys.argv[1]
    print(f"Проверка баланса адреса: {address}")
    
    balance = check_balance(address)
    if balance is not None:
        print(f"Баланс: {balance} BNB")
    else:
        print("Не удалось получить баланс")
