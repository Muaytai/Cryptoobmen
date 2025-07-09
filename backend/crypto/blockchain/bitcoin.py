"""Service for interacting with the Bitcoin blockchain."""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import List, Dict, Any

import requests
from django.conf import settings

from .base import BaseBlockchainService
from bitcoinlib.keys import Key
from bitcoinlib.transactions import Transaction

logger = logging.getLogger(__name__)

# Using a public API for blockchain data. For production, a dedicated node or paid service is recommended.
MEMPOOL_SPACE_API_URL = "https://mempool.space/api"

class BitcoinService(BaseBlockchainService):
    """
    Service for interacting with the Bitcoin blockchain.
    Implements the BaseBlockchainService interface.
    """

    def __init__(self, network: str = 'mainnet'):
        super().__init__(network)
        if self.network not in ['mainnet', 'testnet']:
            raise ValueError("Network must be 'mainnet' or 'testnet'")
        self.mempool_url = MEMPOOL_SPACE_API_URL if network == 'mainnet' else "https://mempool.space/testnet/api"

    def get_transactions(self, address: str, min_timestamp: int = 0) -> List[Dict[str, Any]]:
        """Fetches transactions for a given Bitcoin address from mempool.space."""
        try:
            response = requests.get(f"{self.mempool_url}/address/{address}/txs")
            response.raise_for_status()
            txs = response.json()

            parsed_txs = []
            for transaction in txs:
                # We are interested in incoming transactions
                for vout in transaction.get('vout', []):
                    if vout.get('scriptpubkey_address') == address:
                        parsed_txs.append({
                            'transaction_id': transaction.get('txid'),
                            'from_address': transaction.get('vin')[0].get('prevout', {}).get('scriptpubkey_address', 'unknown'),
                            'to_address': address,
                            'value': str(vout.get('value', 0)),  # Value in satoshis
                            'memo': None
                        })
            return parsed_txs
        except requests.RequestException as e:
            logger.error(f"Error fetching Bitcoin transactions for {address}: {e}")
            return []

    def get_balance(self, address: str) -> Decimal:
        """Gets the balance for a given Bitcoin address from mempool.space."""
        try:
            response = requests.get(f"{self.mempool_url}/address/{address}")
            response.raise_for_status()
            data = response.json()
            balance_satoshi = data.get('chain_stats', {}).get('funded_txo_sum', 0) - \
                              data.get('chain_stats', {}).get('spent_txo_sum', 0)
            return self.from_atomic_unit(balance_satoshi, 8)
        except requests.RequestException as e:
            logger.error(f"Error fetching Bitcoin balance for {address}: {e}")
            return Decimal('0.0')

    def send_transaction(self, private_key_wif: str, to_address: str, amount: Decimal, memo: str = "") -> str:
        """
        Создает и отправляет транзакцию в сети Bitcoin.
        Использует mempool.space для получения UTXO и комиссий.
        """
        try:
            key = Key(private_key_wif, network=self.network)
            from_address = key.address

            utxos_response = requests.get(f"{self.mempool_url}/address/{from_address}/utxo")
            utxos_response.raise_for_status()
            utxos = utxos_response.json()

            if not utxos:
                raise ValueError("No UTXOs found for the address.")

            tx = Transaction(network=self.network)
            
            amount_satoshi = self.to_atomic_unit(amount, 8)
            
            input_total = 0
            # Простая стратегия выбора UTXO: берем входы, пока не покроем сумму
            for utxo in utxos:
                tx.add_input(prev_txid=utxo['txid'], output_n=utxo['vout'], value=utxo['value'])
                input_total += utxo['value']
                if input_total > amount_satoshi:
                    break
            
            # Получаем рекомендованную комиссию
            fees_response = requests.get(f"{self.mempool_url}/v1/fees/recommended")
            fees_response.raise_for_status()
            fees = fees_response.json()
            fee_rate = Decimal(fees.get('halfHourFee', 20))  # sat/vB

            # Приблизительный расчет размера и комиссии
            estimated_size = 10 + len(tx.inputs) * 148 + 2 * 34 
            fee = int(Decimal(estimated_size) * fee_rate)

            if input_total < amount_satoshi + fee:
                raise ValueError(f"Insufficient funds. Have {input_total}, need {amount_satoshi + fee}")

            # Добавляем выходы
            tx.add_output(value=amount_satoshi, address=to_address)
            change = input_total - amount_satoshi - fee
            if change > 546:  # Порог для "пыли"
                tx.add_output(value=change, address=from_address)

            # Подписываем транзакцию
            tx.sign(key)

            # Сериализуем и отправляем
            tx_hex = tx.serialize()
            broadcast_response = requests.post(f"{self.mempool_url}/tx", data=tx_hex)
            broadcast_response.raise_for_status()
            
            return broadcast_response.text

        except requests.RequestException as e:
            logger.error(f"Network error during Bitcoin transaction: {e}")
            raise
        except Exception as e:
            logger.error(f"Error sending Bitcoin transaction: {e}")
            raise
