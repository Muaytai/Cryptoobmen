from django.core.management.base import BaseCommand
from django.conf import settings
from tronpy import Tron
from tronpy.providers import HTTPProvider
import requests

class Command(BaseCommand):
    help = 'Проверяет адрес TRON кошелька в разных сетях'

    def add_arguments(self, parser):
        parser.add_argument(
            'address',
            type=str,
            help='Адрес кошелька для проверки',
        )

    def handle(self, *args, **options):
        address = options['address']
        self.stdout.write(f"=== ПРОВЕРКА АДРЕСА {address} ===")
        
        # Проверяем в тестовой сети Nile
        self.check_address_in_network(address, 'nile')
        
        # Проверяем в основной сети
        self.check_address_in_network(address, 'mainnet')

    def check_address_in_network(self, address, network):
        self.stdout.write(f"\n--- Проверка в сети {network.upper()} ---")
        
        try:
            if network == 'nile':
                api_key = getattr(settings, 'TRONGRID_API_KEY', None)
                if api_key:
                    provider = HTTPProvider(api_key=api_key, endpoint_uri="https://nile.trongrid.io")
                    client = Tron(provider=provider)
                else:
                    client = Tron(network='nile')
                api_url = "https://nile.trongrid.io"
            else:
                client = Tron(network='mainnet')
                api_url = "https://api.trongrid.io"
            
            self.stdout.write(f"✓ Подключение к {network} установлено")
            
            # Проверяем, существует ли аккаунт
            try:
                account_info = client.get_account(address)
                self.stdout.write(f"✓ Аккаунт найден: {account_info}")
                
                # Проверяем баланс TRX
                trx_balance = client.get_account_balance(address)
                self.stdout.write(f"TRX баланс: {trx_balance}")
                
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠️  Аккаунт не найден или ошибка: {e}"))
            
            # Проверяем через API напрямую
            self.check_via_api(address, api_url, network)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Ошибка подключения к {network}: {e}"))

    def check_via_api(self, address, api_url, network):
        self.stdout.write(f"\nПроверка через API {network}:")
        
        try:
            # Проверяем аккаунт через API
            headers = {}
            api_key = getattr(settings, 'TRONGRID_API_KEY', None)
            if api_key:
                headers['TRON-PRO-API-KEY'] = api_key
            
            response = requests.get(
                f"{api_url}/v1/accounts/{address}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.stdout.write(f"✓ API ответ: {response.status_code}")
                if 'data' in data and data['data']:
                    account_data = data['data'][0]
                    self.stdout.write(f"  - Адрес: {account_data.get('address', 'N/A')}")
                    self.stdout.write(f"  - Баланс: {account_data.get('balance', 0)} SUN")
                    self.stdout.write(f"  - Создан: {account_data.get('create_time', 'N/A')}")
                else:
                    self.stdout.write("  - Аккаунт не активирован или не существует")
            else:
                self.stdout.write(f"✗ API ошибка: {response.status_code} - {response.text}")
                
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f"✗ Ошибка API запроса: {e}"))
        
        # Проверяем USDT баланс через контракт
        self.check_usdt_balance(address, api_url, network)

    def check_usdt_balance(self, address, api_url, network):
        contracts = [
            ("TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t", "USDT Nile"),
            ("TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj", "USDT старый Nile"),
        ]
        
        if network == 'mainnet':
            contracts = [
                ("TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t", "USDT Mainnet"),
            ]
        
        for contract_addr, name in contracts:
            try:
                self.stdout.write(f"\nПроверка {name} ({contract_addr}):")
                
                headers = {}
                api_key = getattr(settings, 'TRONGRID_API_KEY', None)
                if api_key:
                    headers['TRON-PRO-API-KEY'] = api_key
                
                # Формируем вызов функции balanceOf
                # Правильно кодируем адрес для параметра
                from tronpy import Tron
                temp_client = Tron(network='nile')
                address_hex = temp_client.address.to_hex(address).replace('0x', '')
                
                payload = {
                    "owner_address": address,
                    "contract_address": contract_addr,
                    "function_selector": "balanceOf(address)",
                    "parameter": address_hex.ljust(64, '0'),  # Дополняем до 64 символов
                    "visible": True
                }
                
                response = requests.post(
                    f"{api_url}/wallet/triggerconstantcontract",
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'constant_result' in data and data['constant_result']:
                        # Конвертируем hex результат в число
                        result_hex = data['constant_result'][0]
                        if result_hex:
                            balance_wei = int(result_hex, 16)
                            balance = balance_wei / (10 ** 6)  # USDT имеет 6 decimals
                            self.stdout.write(f"  ✓ Баланс: {balance} USDT")
                        else:
                            self.stdout.write(f"  - Баланс: 0 USDT")
                    else:
                        self.stdout.write(f"  ✗ Ошибка вызова контракта: {data}")
                else:
                    self.stdout.write(f"  ✗ API ошибка: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.stdout.write(f"  ✗ Ошибка проверки {name}: {e}")
