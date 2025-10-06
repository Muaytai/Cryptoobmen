#!/usr/bin/env python3
import os
import sys
import django

# Настройка Django
sys.path.append('d:\\PythonProjects\\Cryptoobmen\\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from transactions.models import Transaction
from crypto.models import Cryptocurrency
from decimal import Decimal

def check_sol_transactions():
    print("=== Проверка транзакций SOL ===")
    
    try:
        # Получаем валюту SOL
        sol = Cryptocurrency.objects.get(symbol='SOL')
        print(f"Найдена валюта: {sol.name} ({sol.symbol})")
        
        # Получаем последние транзакции SOL
        txs = Transaction.objects.filter(crypto=sol).order_by('-timestamp')[:5]
        print(f"\nПоследние {len(txs)} транзакций SOL:")
        
        for i, tx in enumerate(txs, 1):
            print(f"{i}. {tx.amount} SOL - {tx.status} - {tx.user}")
            print(f"   Хэш: {tx.tx_hash[:30]}..." if tx.tx_hash else "   Хэш: отсутствует")
            print(f"   Дата: {tx.timestamp}")
            print()
            
        # Подсчитываем общее количество транзакций
        total_count = Transaction.objects.filter(crypto=sol).count()
        print(f"Общее количество транзакций SOL: {total_count}")
        
        # Подсчитываем завершенные депозиты
        deposit_count = Transaction.objects.filter(crypto=sol, type='deposit', status='completed').count()
        print(f"Завершенные депозиты SOL: {deposit_count}")
        
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    check_sol_transactions()