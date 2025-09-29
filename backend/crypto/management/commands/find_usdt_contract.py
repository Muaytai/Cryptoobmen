from django.core.management.base import BaseCommand
from django.conf import settings
from tronpy import Tron
from tronpy.providers import HTTPProvider
import requests
import json

class Command(BaseCommand):
    help = 'Находит правильный контракт USDT для данного адреса'

    def add_arguments(self, parser):
        parser.add_argument(
            'address',
            type=str,
            help='Адрес кошелька для проверки',
        )

    def handle(self, *args, **options):
        address = options['address']
        self.stdout.write(f"=== ПОИСК USDT КОНТРАКТОВ ДЛЯ {address} ===")
        
        # Проверяем через TronGrid API
        try:
            api_key = getattr(settings, 'TRONGRID_API_KEY', None)
            headers = {}
            if api_key:
                headers['TRON-PRO-API-KEY'] = api_key
            
            # Получаем все TRC20 токены для адреса
            response = requests.get(
                f"https://nile.trongrid.io/v1/accounts/{address}/tokens",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.stdout.write("✓ Получена информация о токенах:")
                
                if 'data' in data and data['data']:
                    for token_info in data['data']:
                        if 'name' in token_info and 'USDT' in token_info.get('name', '').upper():
                            contract_addr = token_info.get('tokenId', '')
                            balance = int(token_info.get('balance', 0))
                            decimals = int(token_info.get('tokenDecimal', 6))
                            
                            real_balance = balance / (10 ** decimals)
                            
                            self.stdout.write(f"\n🎯 НАЙДЕН USDT!")
                            self.stdout.write(f"   Контракт: {contract_addr}")
                            self.stdout.write(f"   Название: {token_info.get('name', 'N/A')}")
                            self.stdout.write(f"   Символ: {token_info.get('tokenAbbr', 'N/A')}")
                            self.stdout.write(f"   Баланс: {real_balance}")
                            self.stdout.write(f"   Decimals: {decimals}")
                            
                            # Проверяем, совпадает ли баланс с тем, что мы видели
                            if abs(real_balance - 757.1) < 1:
                                self.stdout.write(self.style.SUCCESS("✅ ЭТО ТОТ САМЫЙ КОНТРАКТ!"))
                                self.stdout.write(f"Нужно обновить контракт в БД на: {contract_addr}")
                else:
                    self.stdout.write("❌ Токены не найдены")
            else:
                self.stdout.write(f"❌ Ошибка API: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка: {e}"))
        
        # Также проверим известные контракты
        self.stdout.write(f"\n=== ПРОВЕРКА ИЗВЕСТНЫХ КОНТРАКТОВ ===")
        known_contracts = [
            ("TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t", "USDT Nile Official"),
            ("TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj", "USDT Nile Alternative"),
            ("TG3XXyExBkPp9nzdajDZsozEu4BkaSJozs", "USDT Nile Test"),
            ("TXYZopYOMKUFNuZSNdqcAWMZj3asR9QBLn", "USDT Nile Faucet"),
        ]
        
        for contract_addr, name in known_contracts:
            try:
                self.check_balance_in_contract(address, contract_addr, name)
            except Exception as e:
                self.stdout.write(f"❌ {name}: Ошибка - {e}")

    def check_balance_in_contract(self, address, contract_addr, name):
        try:
            api_key = getattr(settings, 'TRONGRID_API_KEY', None)
            headers = {}
            if api_key:
                headers['TRON-PRO-API-KEY'] = api_key
            
            # Создаем параметр для вызова balanceOf
            from tronpy import Tron
            client = Tron(network='nile')
            
            # Создаем payload для вызова
            payload = {
                "owner_address": address,
                "contract_address": contract_addr,
                "function_selector": "balanceOf(address)",
                "parameter": address,
                "visible": True
            }
            
            response = requests.post(
                "https://nile.trongrid.io/wallet/triggerconstantcontract",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'constant_result' in data and data['constant_result']:
                    result_hex = data['constant_result'][0]
                    if result_hex:
                        balance_wei = int(result_hex, 16)
                        balance = balance_wei / (10 ** 6)  # USDT decimals = 6
                        
                        if balance > 0:
                            self.stdout.write(self.style.SUCCESS(f"✅ {name}: {balance} USDT"))
                            if abs(balance - 757.1) < 1:
                                self.stdout.write(self.style.SUCCESS("🎯 ЭТО ПРАВИЛЬНЫЙ КОНТРАКТ!"))
                        else:
                            self.stdout.write(f"   {name}: 0 USDT")
                    else:
                        self.stdout.write(f"   {name}: 0 USDT")
                else:
                    self.stdout.write(f"❌ {name}: Ошибка вызова")
            else:
                self.stdout.write(f"❌ {name}: API ошибка {response.status_code}")
                
        except Exception as e:
            self.stdout.write(f"❌ {name}: {e}")
