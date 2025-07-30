import logging
from decimal import Decimal
from typing import List, Dict, Any, Tuple
import requests
from bit import PrivateKeyTestnet, PrivateKey
from bit.network import NetworkAPI

from .base import BaseBlockchainService

logger = logging.getLogger(__name__)

class BitcoinService(BaseBlockchainService):
    def __init__(self, network='testnet'):
        super().__init__(network)
        self.coin_symbol = 'btc-testnet' if network == 'testnet' else 'btc'
        
        # Используем Blockstream API
        if network == 'testnet':
            self.api_url = 'https://blockstream.info/testnet/api'
        else:
            self.api_url = 'https://blockstream.info/api'

    def get_transactions(self, address: str, min_timestamp: int = 0) -> List[Dict[str, Any]]:
        """Получает транзакции для адреса используя Blockstream API."""
        try:
            # Используем Blockstream API
            url = f"{self.api_url}/address/{address}/txs"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            transactions = response.json()
            txs = []
            
            for tx in transactions:
                # Проверяем входящие транзакции
                for vout in tx.get('vout', []):
                    if vout.get('scriptpubkey_address') == address:
                        # Проверяем подтверждение транзакции
                        confirmed = tx.get('status', {}).get('confirmed', False)
                        block_height = tx.get('status', {}).get('block_height')
                        
                        txs.append({
                            'transaction_id': tx['txid'],
                            'value': str(vout['value']),  # В сатоши
                            'memo': None,
                            'block_height': block_height,
                            'confirmed': confirmed
                        })
            
            return txs
        except Exception as e:
            logger.error(f"Error getting transactions for {address}: {e}")
            return []

    def send_transaction(self, private_key: str, to_address: str, amount: Decimal, memo: str = "") -> str:
        """Отправляет транзакцию Bitcoin."""
        try:
            # Создаем объект приватного ключа
            if self.network == 'testnet':
                key = PrivateKeyTestnet(private_key)
            else:
                key = PrivateKey(private_key)
            
            # Конвертируем amount в сатоши
            amount_satoshi = int(amount * Decimal('100000000'))
            
            # Отправляем транзакцию
            tx_hash = key.send([(to_address, amount_satoshi, 'satoshi')])
            
            logger.info(f"Bitcoin transaction sent: {tx_hash}")
            return tx_hash
            
        except Exception as e:
            logger.error(f"Error sending Bitcoin transaction: {e}")
            raise Exception(f"Failed to send Bitcoin transaction: {e}")

    def get_balance(self, address: str) -> Decimal:
        """Получает баланс адреса."""
        try:
            url = f"{self.api_url}/address/{address}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            # Баланс в сатоши, конвертируем в BTC
            balance_satoshi = data.get('chain_stats', {}).get('funded_txo_sum', 0) - \
                             data.get('chain_stats', {}).get('spent_txo_sum', 0)
            
            return Decimal(balance_satoshi) / Decimal('100000000')
        except Exception as e:
            logger.error(f"Error getting balance for {address}: {e}")
            return Decimal('0.0')

    def create_new_address(self, **kwargs) -> Tuple[str, str]:
        """Создает новый адрес и возвращает его вместе с приватным ключом."""
        try:
            # Создаем новый приватный ключ
            if self.network == 'testnet':
                key = PrivateKeyTestnet()
            else:
                key = PrivateKey()
            
            address = key.address
            private_key_wif = key.to_wif()
            
            logger.info(f"Created new Bitcoin address: {address}")
            return address, private_key_wif
            
        except Exception as e:
            logger.error(f"Error creating Bitcoin address: {e}")
            raise Exception(f"Failed to create Bitcoin address: {e}")

    def validate_address(self, address: str) -> bool:
        """Валидирует Bitcoin адрес."""
        try:
            # Простая валидация длины и префикса
            if self.network == 'testnet':
                # Testnet адреса начинаются с 'm', 'n', '2' или 'tb1'
                valid_prefixes = ('m', 'n', '2', 'tb1')
            else:
                # Mainnet адреса начинаются с '1', '3' или 'bc1'
                valid_prefixes = ('1', '3', 'bc1')
            
            if not address or len(address) < 26 or len(address) > 62:
                return False
                
            return address.startswith(valid_prefixes)
            
        except Exception as e:
            logger.error(f"Error validating address {address}: {e}")
            return False
