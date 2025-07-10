#!/usr/bin/env python3
"""
Скрипт для тестирования подключения к Ethereum API.
Проверяет подключение к RPC и Etherscan API.
"""

import os
import sys
import requests
from web3 import Web3
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('.env.backend')

def test_ethereum_rpc():
    """Тестирует подключение к Ethereum RPC."""
    print("🔍 Тестирование подключения к Ethereum RPC...")
    
    rpc_url = os.getenv('ETHEREUM_RPC_URL')
    if not rpc_url:
        print("❌ ETHEREUM_RPC_URL не установлен")
        return False
    
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not w3.is_connected():
            print(f"❌ Не удалось подключиться к RPC: {rpc_url}")
            return False
        
        # Получаем номер последнего блока
        latest_block = w3.eth.block_number
        print(f"✅ Подключение к RPC успешно")
        print(f"   Последний блок: {latest_block}")
        
        # Получаем информацию о сети
        chain_id = w3.eth.chain_id
        network_name = {
            1: "Mainnet",
            3: "Ropsten",
            4: "Rinkeby",
            5: "Goerli",
            11155111: "Sepolia"
        }.get(chain_id, f"Unknown ({chain_id})")
        
        print(f"   Сеть: {network_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к RPC: {e}")
        return False

def test_etherscan_api():
    """Тестирует подключение к Etherscan API."""
    print("\n🔍 Тестирование подключения к Etherscan API...")
    
    api_key = os.getenv('ETHERSCAN_API_KEY')
    if not api_key:
        print("❌ ETHERSCAN_API_KEY не установлен")
        return False
    
    network = os.getenv('ETHEREUM_NETWORK', 'mainnet')
    
    # Определяем URL API в зависимости от сети
    if network == 'sepolia':
        api_url = "https://api-sepolia.etherscan.io/api"
    elif network == 'goerli':
        api_url = "https://api-goerli.etherscan.io/api"
    else:  # mainnet
        api_url = "https://api.etherscan.io/api"
    
    try:
        # Тестируем API запросом баланса известного адреса
        test_address = "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"  # Binance hot wallet
        
        params = {
            "module": "account",
            "action": "balance",
            "address": test_address,
            "tag": "latest",
            "apikey": api_key
        }
        
        response = requests.get(api_url, params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ HTTP ошибка {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        
        if data.get("status") != "1":
            print(f"❌ API ошибка: {data.get('message', 'Unknown error')}")
            return False
        
        balance_wei = int(data.get("result", "0"))
        balance_eth = balance_wei / (10 ** 18)
        
        print(f"✅ Подключение к Etherscan API успешно")
        print(f"   Сеть: {network}")
        print(f"   Тестовый адрес: {test_address}")
        print(f"   Баланс: {balance_eth:.6f} ETH")
        
        return True
        
    except requests.Timeout:
        print("❌ Таймаут при запросе к Etherscan API")
        return False
    except requests.RequestException as e:
        print(f"❌ Ошибка запроса к Etherscan API: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_usdt_contract():
    """Тестирует доступ к контракту USDT."""
    print("\n🔍 Тестирование контракта USDT...")
    
    rpc_url = os.getenv('ETHEREUM_RPC_URL')
    if not rpc_url:
        print("❌ ETHEREUM_RPC_URL не установлен")
        return False
    
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Адрес контракта USDT на Ethereum
        usdt_address = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
        
        # Простой ABI для проверки баланса
        abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }
        ]
        
        contract = w3.eth.contract(address=usdt_address, abi=abi)
        
        # Тестируем вызов функции balanceOf
        test_address = "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
        balance = contract.functions.balanceOf(test_address).call()
        
        balance_usdt = balance / (10 ** 6)  # USDT имеет 6 десятичных знаков
        
        print(f"✅ Контракт USDT доступен")
        print(f"   Адрес контракта: {usdt_address}")
        print(f"   Тестовый адрес: {test_address}")
        print(f"   Баланс USDT: {balance_usdt:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при работе с контрактом USDT: {e}")
        return False

def main():
    """Основная функция тестирования."""
    print("🚀 Тестирование подключения к Ethereum API")
    print("=" * 50)
    
    # Проверяем переменные окружения
    print("📋 Проверка переменных окружения:")
    rpc_url = os.getenv('ETHEREUM_RPC_URL')
    api_key = os.getenv('ETHERSCAN_API_KEY')
    network = os.getenv('ETHEREUM_NETWORK', 'mainnet')
    
    print(f"   ETHEREUM_RPC_URL: {'✅' if rpc_url else '❌'}")
    print(f"   ETHERSCAN_API_KEY: {'✅' if api_key else '❌'}")
    print(f"   ETHEREUM_NETWORK: {network}")
    
    if not rpc_url or not api_key:
        print("\n❌ Не все необходимые переменные окружения установлены")
        print("   Создайте файл .env.backend с необходимыми переменными")
        sys.exit(1)
    
    # Тестируем подключения
    rpc_ok = test_ethereum_rpc()
    etherscan_ok = test_etherscan_api()
    usdt_ok = test_usdt_contract()
    
    print("\n" + "=" * 50)
    print("📊 Результаты тестирования:")
    print(f"   Ethereum RPC: {'✅' if rpc_ok else '❌'}")
    print(f"   Etherscan API: {'✅' if etherscan_ok else '❌'}")
    print(f"   USDT Contract: {'✅' if usdt_ok else '❌'}")
    
    if rpc_ok and etherscan_ok and usdt_ok:
        print("\n🎉 Все тесты пройдены успешно!")
        print("   Система готова к работе с Ethereum")
        return True
    else:
        print("\n❌ Некоторые тесты не пройдены")
        print("   Проверьте настройки и попробуйте снова")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 