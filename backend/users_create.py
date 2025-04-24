#!/usr/bin/env python
"""
Скрипт создания тестовых пользователей для проекта
"""
import os
import sys
import argparse
import random
import string
import django
from datetime import datetime, timedelta

# Настройка Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

# Импорт моделей Django
from django.contrib.auth import get_user_model
from django.db import transaction
from django.contrib.auth.models import Group

User = get_user_model()

def generate_password(length=10):
    """Генерирует случайный пароль заданной длины"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(random.choice(chars) for _ in range(length))

def create_test_users(count=10, force=False):
    """
    Создает тестовых пользователей
    :param count: Количество пользователей для создания
    :param force: Пропускать подтверждение
    """
    # Проверяем, существуют ли уже тестовые пользователи
    existing_users = User.objects.filter(email__startswith='test_user').count()
    
    if existing_users > 0 and not force:
        confirm = input(f"В базе уже существует {existing_users} тестовых пользователей. Создать еще {count}? (y/n): ")
        if confirm.lower() != 'y':
            print("Отмена создания пользователей.")
            return
    
    # Создаем список новых пользователей
    new_users = []
    admin_password = "admin123!"
    
    # Создаем admin пользователя, если не существует
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
        }
    )
    
    if created:
        admin_user.set_password(admin_password)
        admin_user.save()
        print(f"✓ Создан администратор: admin@example.com с паролем: {admin_password}")
    
    with transaction.atomic():
        # Создаем обычных пользователей
        for i in range(1, count + 1):
            username = f"test_user{i}"
            email = f"test_user{i}@example.com"
            password = generate_password(8)
            
            # Проверяем, существует ли пользователь
            if User.objects.filter(username=username).exists():
                print(f"✓ Пользователь {username} уже существует, пропускаем")
                continue
                
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=f"Test{i}",
                last_name=f"User{i}",
                is_active=True
            )
            
            # Устанавливаем даты для более реалистичных данных
            user.date_joined = datetime.now() - timedelta(days=random.randint(1, 30))
            user.save()
            
            new_users.append((username, email, password))
            
    print(f"\nСоздано {len(new_users)} новых тестовых пользователей:")
    for username, email, password in new_users:
        print(f"- {username} ({email}): {password}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Создание тестовых пользователей')
    parser.add_argument('-c', '--count', type=int, default=10, help='Количество пользователей для создания')
    parser.add_argument('-f', '--force', action='store_true', help='Пропустить подтверждение')
    
    args = parser.parse_args()
    
    print(f"Создаем {args.count} тестовых пользователей...")
    create_test_users(args.count, args.force) 