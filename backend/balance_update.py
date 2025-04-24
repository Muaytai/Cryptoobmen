#!/usr/bin/env python
"""
Запуск скрипта обновления балансов кошельков
"""
import os
import sys
import argparse

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.update_balances import update_wallet_balances

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Обновление балансов криптовалютных кошельков')
    parser.add_argument('--min-btc', type=float, default=0.001, help='Минимальный баланс BTC')
    parser.add_argument('--max-btc', type=float, default=1.0, help='Максимальный баланс BTC')
    parser.add_argument('--min-eth', type=float, default=0.01, help='Минимальный баланс ETH')
    parser.add_argument('--max-eth', type=float, default=10.0, help='Максимальный баланс ETH')
    parser.add_argument('--min-usdt', type=float, default=10.0, help='Минимальный баланс USDT')
    parser.add_argument('--max-usdt', type=float, default=1000.0, help='Максимальный баланс USDT')
    
    args = parser.parse_args()
    
    print(f"Обновление балансов кошельков...")
    update_wallet_balances(
        args.min_btc, args.max_btc,
        args.min_eth, args.max_eth,
        args.min_usdt, args.max_usdt
    ) 