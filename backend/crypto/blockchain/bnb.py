from decimal import Decimal
from typing import List, Dict, Any
from .base import BaseBlockchainService
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class BNBService(BaseBlockchainService):
    """
    Сервис для работы с Binance Smart Chain (BSC) Testnet
    """
    
    def __init__(self, network: str = 'testnet'):
        super().__init__(network)
        self.network = network
        # BSC Testnet RPC endpoint
        self.rpc_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"
        self.chain_id = 97  # BSC Testnet chain ID
        
    def get_transactions(self, address: str, min_timestamp: int = 0, contract_address: str = None) -> List[Dict[str, Any]]:
        """
        Получает входящие транзакции для BSC Testnet адреса
        """
        try:
            # Используем Etherscan API для BSC Testnet (chainid=97)
            api_key = settings.BSCSCAN_API_KEY
            if not api_key:
                logger.warning("BSCScan API key not configured")
                return []
                
            if contract_address:
                # ERC-20 токен транзакции
                url = "https://api.etherscan.io/v2/api"
                params = {
                    'chainid': 97,  # BSC Testnet
                    'module': 'account',
                    'action': 'tokentx',
                    'contractaddress': contract_address,
                    'address': address,
                    'startblock': 0,
                    'endblock': 99999999,
                    'sort': 'desc',
                    'apikey': api_key
                }
            else:
                # Нативные BNB транзакции
                url = "https://api.etherscan.io/v2/api"
                params = {
                    'chainid': 97,  # BSC Testnet
                    'module': 'account',
                    'action': 'txlist',
                    'address': address,
                    'startblock': 0,
                    'endblock': 99999999,
                    'sort': 'desc',
                    'apikey': api_key
                }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] != '1':
                logger.warning(f"BSCScan API error: {data.get('message', 'Unknown error')}")
                return []
            
            transactions = []
            for tx in data['result']:
                # Фильтруем только входящие транзакции
                if tx['to'].lower() == address.lower():
                    transactions.append({
                        'transaction_id': tx['hash'],
                        'from_address': tx['from'],
                        'to_address': tx['to'],
                        'value': tx['value'],
                        'memo': '',  # BSC не поддерживает memo
                        'timestamp': int(tx['timeStamp']) * 1000,  # Конвертируем в миллисекунды
                        'block_number': tx['blockNumber']
                    })
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error fetching BSC transactions: {e}")
            return []
    
    def send_transaction(self, private_key: str, to_address: str, amount: Decimal, memo: str = "", contract_address: str = None) -> str:
        """
        Отправляет транзакцию в BSC Testnet
        """
        try:
            from web3 import Web3
            from eth_account import Account
            
            w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            
            if not w3.is_connected():
                raise Exception("Cannot connect to BSC Testnet")
            
            account = Account.from_key(private_key)
            from_address = account.address
            
            # Получаем nonce
            nonce = w3.eth.get_transaction_count(from_address)
            
            if contract_address:
                # ERC-20 токен транзакция
                # Здесь нужно реализовать transfer функцию ERC-20
                # Упрощенная версия для примера
                raise NotImplementedError("ERC-20 token transfers not implemented yet")
            else:
                # Нативная BNB транзакция
                transaction = {
                    'to': to_address,
                    'value': w3.to_wei(amount, 'ether'),
                    'gas': 21000,
                    'gasPrice': w3.eth.gas_price,
                    'nonce': nonce,
                    'chainId': self.chain_id
                }
            
            # Подписываем транзакцию
            signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
            
            # Отправляем транзакцию
            # Поддержка старых и новых версий web3.py
            raw_tx = getattr(signed_txn, 'raw_transaction', None) or getattr(signed_txn, 'rawTransaction', None)
            tx_hash = w3.eth.send_raw_transaction(raw_tx)
            
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Error sending BSC transaction: {e}")
            raise
    
    def get_balance(self, address: str) -> Decimal:
        """
        Получает баланс BNB на адресе
        """
        try:
            from web3 import Web3
            
            w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            
            if not w3.is_connected():
                raise Exception("Cannot connect to BSC Testnet")
            
            balance_wei = w3.eth.get_balance(address)
            balance_bnb = w3.from_wei(balance_wei, 'ether')
            
            return Decimal(str(balance_bnb))
            
        except Exception as e:
            logger.error(f"Error getting BSC balance: {e}")
            return Decimal('0')
    
    def create_new_address(self, **kwargs) -> tuple:
        """
        Создает новый BSC адрес
        """
        try:
            from eth_account import Account
            
            account = Account.create()
            address = account.address
            private_key = account.key.hex()
            
            return address, private_key
            
        except Exception as e:
            logger.error(f"Error creating BSC address: {e}")
            raise
    
    def is_transaction_confirmed(self, tx_hash: str) -> bool:
        """
        Проверяет подтверждение транзакции в BSC
        """
        try:
            from web3 import Web3
            
            w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            
            if not w3.is_connected():
                return False
            
            tx = w3.eth.get_transaction(tx_hash)
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            
            # Проверяем, что транзакция успешна
            return receipt.status == 1
            
        except Exception as e:
            logger.error(f"Error checking BSC transaction confirmation: {e}")
            return False