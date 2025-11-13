#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для ручного создания депозитной транзакции в базе данных.
Используется для testnet когда транзакция не обнаруживается автоматически.
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from crypto.models import UserWallet, Cryptocurrency
from transactions.models import Transaction, Deposit
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

# Данные из вашего случая
user_id = 7
currency_symbol = 'BNB'
currency_network = 'BEP20'
deposit_address = '0xf9a1877FF0f1BB13cA68Db57f4fD88D0Ef96483b'
amount = Decimal('0.002')  # 0.002 tBNB

print("=" * 60)
print("Создание ручной депозитной транзакции")
print("=" * 60)

try:
    # Получаем пользователя
    user = User.objects.get(id=user_id)
    print(f"Пользователь: {user.email}")
    
    # Получаем валюту
    currency = Cryptocurrency.objects.get(symbol=currency_symbol, network=currency_network)
    print(f"Валюта: {currency}")
    
    # Получаем кошелёк
    wallet = UserWallet.objects.get(user=user, currency=currency)
    print(f"Кошелёк: {wallet}")
    print(f"Текущий баланс: {wallet.balance} {currency_symbol}")
    print(f"Адрес депозита: {wallet.deposit_address}")
    
    # Создаём транзакцию
    transaction = Transaction.objects.create(
        user=user,
        crypto=currency,
        amount=amount,
        fee=Decimal('0'),
        type='deposit',
        status='completed',  # Сразу завершенная для testnet
        tx_hash='MANUAL_TESTNET_' + deposit_address[:20],  # Фейковый хеш для testnet
        timestamp=timezone.now(),
        notes='Manual testnet deposit'
    )
    print(f"\n✅ Транзакция создана: ID={transaction.id}, Hash={transaction.tx_hash}")
    
    # Создаём объект депозита
    deposit = Deposit.objects.create(
        user=user,
        transaction=transaction,
        wallet=wallet,
        address=deposit_address,
        confirmed=True,
        confirmation_date=timezone.now()
    )
    print(f"✅ Депозит создан: ID={deposit.id}")
    
    # Обновляем баланс пользователя
    wallet.balance += amount
    wallet.save()
    print(f"✅ Баланс обновлён: {wallet.balance} {currency_symbol}")
    
    print("\n" + "=" * 60)
    print("УСПЕШНО! Транзакция создана в базе данных.")
    print("Проверьте в админ-панели Django:")
    print(f"http://localhost:8000/admin/transactions/transaction/{transaction.id}/")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

