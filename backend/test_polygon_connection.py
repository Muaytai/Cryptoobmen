#!/usr/bin/env python3
"""
Скрипт для проверки подключения к правильной сети Polygon
"""
import os
import sys
import django

# Добавляем путь к проекту
sys.path.append('/home/chaizer/projects/Cryptoobmen/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from crypto.blockchain.polygon import PolygonService

def check_polygon_connection():
    """Проверка подключения к Polygon"""
    print("🔍 Проверка подключения к Polygon...")
    
    try:
        service = PolygonService()
        
        # Основная информация
        chain_id = service.w3.eth.chain_id
        current_block = service.w3.eth.block_number
        network = service.network
        rpc_url = service.w3.provider.endpoint_uri
        
        print(f"📊 Информация о подключении:")
        print(f"   Chain ID: {chain_id}")
        print(f"   Network: {network}")
        print(f"   Current block: {current_block}")
        print(f"   RPC URL: {rpc_url}")
        
        # Проверка на правильную сеть
        if chain_id == 80002:
            print("✅ Подключен к Polygon Amoy testnet (правильно!)")
        elif chain_id == 137:
            print("❌ Подключен к Polygon mainnet (неправильно! Нужен testnet)")
            return False
        else:
            print(f"⚠️ Подключен к неизвестной сети с Chain ID: {chain_id}")
            return False
        
        # Тестируем баланс
        test_address = "0x29A1B48e60782872D9f9dC48D120f04B8Bbe512C"
        print(f"\n🔍 Проверка баланса тестового адреса: {test_address}")
        
        balance = service.get_balance(test_address)
        print(f"   Баланс: {balance} POL")
        
        if balance > 0:
            print("✅ Адрес имеет баланс в testnet")
        else:
            print("⚠️ Баланс нулевой - возможно адрес в другой сети")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    success = check_polygon_connection()
    if success:
        print("\n🎉 Подключение к Polygon настроено правильно!")
    else:
        print("\n💥 Требуется исправление настроек подключения!")
    sys.exit(0 if success else 1)
