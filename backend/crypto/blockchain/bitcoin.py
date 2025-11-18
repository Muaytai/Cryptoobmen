import logging
from decimal import Decimal
from typing import List, Dict, Any, Tuple
import requests
from django.conf import settings
from bit import PrivateKeyTestnet, PrivateKey
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes

from .base import BaseBlockchainService

logger = logging.getLogger(__name__)

class BitcoinService(BaseBlockchainService):
    def __init__(self, network='testnet'):
        super().__init__(network)
        self.coin_symbol = 'btc-testnet' if network == 'testnet' else 'btc'
        
        if network == 'testnet':
            self.api_url = 'https://blockstream.info/testnet/api'
            self.bip44_coin = Bip44Coins.BITCOIN_TESTNET
        else:
            self.api_url = 'https://blockstream.info/api'
            self.bip44_coin = Bip44Coins.BITCOIN

    def get_transactions(self, address: str, min_timestamp: int = 0) -> List[Dict[str, Any]]:
        """Получает транзакции для адреса используя Blockstream API."""
        try:
            url = f"{self.api_url}/address/{address}/txs"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            transactions = response.json()
            txs = []
            
            for tx in transactions:
                for vout in tx.get('vout', []):
                    if vout.get('scriptpubkey_address') == address:
                        confirmed = tx.get('status', {}).get('confirmed', False)
                        if not confirmed:
                            continue # Пропускаем неподтвержденные
                        
                        txs.append({
                            'transaction_id': tx['txid'],
                            'value': str(vout['value']),  # В сатоши
                            'memo': None,
                        })
            return txs
        except Exception as e:
            logger.error(f"Error getting Bitcoin transactions for {address}: {e}")
            return []

    def send_transaction(self, private_key: str, to_address: str, amount: Decimal, **kwargs) -> str:
        """Отправляет транзакцию Bitcoin. Умеет отправлять всю сумму (sweep)."""
        try:
            if self.network == 'testnet':
                key = PrivateKeyTestnet(private_key)
            else:
                key = PrivateKey(private_key)
            
            unspents = key.get_unspents()
            if not unspents:
                logger.warning(f"No unspents available for {key.address}, skipping send.")
                return None

            if amount == Decimal('0.0'):
                amount_satoshi = sum(int(u.amount) for u in unspents)
            else:
                amount_satoshi = int(amount * Decimal('100000000'))

            outputs = [(to_address, amount_satoshi, 'satoshi')]
            tx_hex = key.create_transaction(
                outputs,
                fee=None,
                leftover=to_address,
                unspents=unspents or None,
            )

            tx_hash = self._broadcast_transaction(tx_hex)
            
            logger.info(f"Bitcoin transaction sent from {key.address}: {tx_hash}")
            return tx_hash
            
        except Exception as e:
            logger.error(f"Error sending Bitcoin transaction: {e}", exc_info=True)
            raise Exception(f"Failed to send Bitcoin transaction: {e}")

    def get_balance(self, address: str) -> Decimal:
        """Получает баланс адреса."""
        try:
            url = f"{self.api_url}/address/{address}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            balance_satoshi = data.get('chain_stats', {}).get('funded_txo_sum', 0) - \
                             data.get('chain_stats', {}).get('spent_txo_sum', 0)
            return Decimal(balance_satoshi) / Decimal('100000000')
        except Exception as e:
            logger.error(f"Error getting balance for {address}: {e}")
            return Decimal('0.0')

    def is_transaction_confirmed(self, tx_hash: str) -> bool:
        """Проверяет, подтверждена ли транзакция в Blockstream API."""
        try:
            url = f"{self.api_url}/tx/{tx_hash}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('status', {}).get('confirmed', False)
        except Exception as e:
            logger.error(f"Error checking Bitcoin transaction {tx_hash}: {e}")
            return False

    def _broadcast_transaction(self, tx_hex: str) -> str:
        """Публикует транзакцию через BlockCypher API, чтобы гарантировать доставку."""
        token = getattr(settings, 'BLOCKCYPHER_API_KEY', '')
        network_path = "test3" if self.network == 'testnet' else "main"
        url = f"https://api.blockcypher.com/v1/btc/{network_path}/txs/push"
        payload = {"tx": tx_hex}
        if token:
            payload["token"] = token

        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        tx = data.get("tx") or {}
        tx_hash = tx.get("hash") or data.get("hash")
        if not tx_hash:
            raise ValueError("BlockCypher response did not contain transaction hash.")
        return tx_hash

    def create_new_address(self, user_id: int, **kwargs) -> Tuple[str, str]:
        """Создает новый адрес и приватный ключ для пользователя, используя HD-генерацию."""
        try:
            master_seed_hex = getattr(settings, 'BITCOIN_MASTER_SEED_HEX', None)
            if not master_seed_hex:
                raise ValueError("BITCOIN_MASTER_SEED_HEX is not configured in settings.")

            seed_bytes = bytes.fromhex(master_seed_hex)
            bip44_mst = Bip44.FromSeed(seed_bytes, self.bip44_coin)
            
            # Используем timestamp для генерации уникальных адресов при ротации
            import time
            timestamp_index = int(time.time()) % 1000000  # Последние 6 цифр timestamp для уникальности
            unique_index = (user_id * 1000000) + timestamp_index  # Комбинируем user_id с timestamp
            
            # Путь: m/44'/<coin_type>'/0'/0/<unique_index>
            bip44_acc = bip44_mst.Purpose().Coin().Account(0)
            bip44_chg = bip44_acc.Change(Bip44Changes.CHAIN_EXT)
            bip44_addr = bip44_chg.AddressIndex(unique_index)

            # bip_utils v3+ не имеет метода Address(), нужно дергать публичный ключ
            address = bip44_addr.PublicKey().ToAddress()
            private_key_wif = bip44_addr.PrivateKey().ToWif()
            
            logger.info(f"Generated new Bitcoin address for user {user_id} (index {unique_index}): {address}")
            return address, private_key_wif
            
        except Exception as e:
            logger.error(f"Error creating HD Bitcoin address for user {user_id}: {e}", exc_info=True)
            raise Exception(f"Failed to create HD Bitcoin address: {e}")
