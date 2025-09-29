#!/usr/bin/env python3
"""
Скрипт для исправления балансов пользователей после ошибки с консолидацией
"""

import os
import django
from decimal import Decimal

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import transaction
from django.db.models import Sum
from crypto.models import UserWallet
from transactions.models import Transaction
from django.contrib.auth import get_user_model

User = get_user_model()

def fix_user_balance(user_id):
    """Исправляет баланс конкретного пользователя"""
    
    print(f'🔧 Исправление баланса User {user_id}...')
    
    try:
        user = User.objects.get(id=user_id)
        wallet = UserWallet.objects.get(user=user, currency__symbol='POL')
        
        print(f'Текущий баланс: {wallet.balance} POL')
        
        # Считаем правильный баланс
        deposits = Transaction.objects.filter(
            user=user,
            crypto__symbol='POL',
            type='deposit',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        withdrawals = Transaction.objects.filter(
            user=user,
            crypto__symbol='POL',
            type='withdrawal',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        consolidations = Transaction.objects.filter(
            user=user,
            crypto__symbol='POL',
            type='consolidation',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        correct_balance = deposits - withdrawals - consolidations
        
        print(f'\n📊 Расчет правильного баланса:')
        print(f'+ Депозиты: {deposits} POL')
        print(f'- Выводы: {withdrawals} POL')
        print(f'- Консолидации: {consolidations} POL')
        print(f'= Правильный баланс: {correct_balance} POL')
        
        difference = wallet.balance - correct_balance
        print(f'\n💰 Текущий баланс: {wallet.balance} POL')
        print(f'🎯 Разница: {difference} POL')
        
        if abs(difference) < Decimal('0.00000001'):
            print('✅ Баланс уже корректный!')
            return True
            
        # Применяем исправление
        confirm = input(f'\nИсправить баланс с {wallet.balance} на {correct_balance} POL? (y/N): ')
        if confirm.lower() == 'y':
            with transaction.atomic():
                wallet.balance = correct_balance
                wallet.save()
                
                print(f'✅ Баланс исправлен!')
                print(f'Новый баланс: {wallet.balance} POL')
                return True
        else:
            print('❌ Исправление отменено')
            return False
            
    except Exception as e:
        print(f'❌ Ошибка: {e}')
        return False

def audit_all_users():
    """Проверяет балансы всех пользователей с POL"""
    
    print('🔍 Аудит балансов всех пользователей...')
    
    pol_wallets = UserWallet.objects.filter(
        currency__symbol='POL',
        user__isnull=False
    ).select_related('user', 'currency')
    
    problems_found = 0
    
    for wallet in pol_wallets:
        user = wallet.user
        
        # Считаем правильный баланс
        deposits = Transaction.objects.filter(
            user=user,
            crypto__symbol='POL',
            type='deposit',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        withdrawals = Transaction.objects.filter(
            user=user,
            crypto__symbol='POL',
            type='withdrawal',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        consolidations = Transaction.objects.filter(
            user=user,
            crypto__symbol='POL',
            type='consolidation',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        correct_balance = deposits - withdrawals - consolidations
        difference = wallet.balance - correct_balance
        
        if abs(difference) > Decimal('0.00000001'):
            problems_found += 1
            print(f'\n⚠️ User {user.id}:')
            print(f'   Текущий: {wallet.balance} POL')
            print(f'   Правильный: {correct_balance} POL')
            print(f'   Разница: {difference} POL')
    
    if problems_found == 0:
        print('\n✅ Все балансы корректны!')
    else:
        print(f'\n⚠️ Найдено {problems_found} проблем с балансами')
    
    return problems_found

if __name__ == '__main__':
    print('🏥 Скрипт исправления балансов пользователей')
    print('=' * 50)
    
    choice = input('\n1. Проверить всех пользователей\n2. Исправить конкретного пользователя\nВыберите (1/2): ')
    
    if choice == '1':
        audit_all_users()
    elif choice == '2':
        user_id = input('Введите ID пользователя: ')
        try:
            fix_user_balance(int(user_id))
        except ValueError:
            print('❌ Неверный ID пользователя')
    else:
        print('❌ Неверный выбор')
