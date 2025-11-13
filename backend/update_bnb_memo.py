#!/usr/bin/env python
"""
Скрипт для обновления BNB cryptocurrency records
Устанавливает requires_memo=False для BNB в сети BEP20
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from crypto.models import Cryptocurrency

# Находим BNB в сети BEP20
bnb = Cryptocurrency.objects.filter(symbol='BNB', network='BEP20').first()

if bnb:
    print(f'Найдена валюта: {bnb.name} ({bnb.symbol} {bnb.network})')
    print(f'Текущий requires_memo: {bnb.requires_memo}')
    
    if bnb.requires_memo:
        bnb.requires_memo = False
        bnb.save()
        print('✓ requires_memo установлен в False')
    else:
        print('✓ requires_memo уже установлен в False')
else:
    print('⚠ BNB в сети BEP20 не найдена в базе данных')






