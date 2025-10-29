"""Service for interacting with the Tron blockchain (TRC20 tokens)."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
import json
from decimal import Decimal

import requests
from tronpy import Tron
from tronpy.providers import HTTPProvider
from tronpy.keys import PrivateKey
from tronpy.contract import Contract
from django.conf import settings
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes

from .base import BaseBlockchainService

logger = logging.getLogger(__name__)

# Contract address for USDT on TRON (TRC20)
USDT_CONTRACT = settings.USDT_TRC20_CONTRACT_ADDRESS

class TronGridError(RuntimeError):
    """Raised when TronGrid returns an error."""

# Стандартный ABI для токенов TRC20, включая функцию transfer
TRC20_ABI = """
[
    {
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]
"""

class TronService(BaseBlockchainService):
    """
    Service for interacting with the Tron blockchain.
    Implements the BaseBlockchainService interface.
    """

    def __init__(self, network: str = 'nile'):
        super().__init__(network)
        self.api_key = settings.TRONGRID_API_KEY
        self.bip44_coin = Bip44Coins.TRON

        current_network = self.network.lower()
        if current_network in ['nile', 'trc20', 'tron']:
            # Предпочитаем URL из настроек, иначе дефолтный
            nile_api_url = getattr(settings, 'TRON_API_URL', 'https://api.nile.trongrid.io')
            self.api_url = nile_api_url
            self.client = Tron(provider=HTTPProvider(api_key=self.api_key, endpoint_uri=nile_api_url))
            self.network = 'nile'
        else:
            # Assume mainnet for anything else
            self.api_url = settings.TRON_API_URL
            self.client = Tron(network='mainnet')
            self.network = 'mainnet'

    def _headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["TRON-PRO-API-KEY"] = self.api_key
        return headers

    def _get_transaction_by_id(self, tx_id: str) -> Dict[str, Any]:
        url = f"{self.api_url}/wallet/gettransactionbyid"
        payload = {"value": tx_id}
        try:
            resp = requests.post(url, json=payload, headers=self._headers(), timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.exception(f"[_get_transaction_by_id] Unexpected error for tx_id {tx_id}: {e}")
            raise TronGridError(f"Failed to get transaction {tx_id}: {e}")

    def get_transactions(self, address: str, min_timestamp: int = 0, contract_address: str = None) -> List[Dict[str, Any]]:
        """Fetches TRC20 transfers or native TRX transfers to *address* after *min_timestamp* (ms)."""
        if not address or not address.startswith('T') or len(address) != 34:
            logger.warning(f"[TRON] Skipping invalid address: {address}")
            return []

        # Если contract_address НЕ передан или пустая строка, то ищем нативные TRX транзакции
        if not contract_address or contract_address.strip() == "":
            return self._get_native_trx_transactions(address, min_timestamp)
        
        # Если contract_address передан, то ищем TRC20 токены
        return self._get_trc20_transactions(address, min_timestamp, contract_address)

    def _get_trc20_transactions(self, address: str, min_timestamp: int, contract_address: str) -> List[Dict[str, Any]]:
        """Fetches TRC20 token transfers."""
        url = f"{self.api_url}/v1/accounts/{address}/transactions/trc20"
        params = {
            "only_to": "true",
            "limit": 100,
            "min_timestamp": min_timestamp,
            "contract_address": contract_address
        }
        
        try:
            resp = requests.get(url, params=params, headers=self._headers(), timeout=20)
            resp.raise_for_status()
            data = resp.json()

            if not data.get("success", False):
                raise TronGridError(str(data))

            return data.get("data", [])

        except requests.RequestException as e:
            logger.error(f"Request to TronGrid failed for TRC20: {e}")
            raise TronGridError(f"TronGrid TRC20 request failed: {e}")

    def _get_native_trx_transactions(self, address: str, min_timestamp: int) -> List[Dict[str, Any]]:
        """Fetches native TRX transfers."""
        url = f"{self.api_url}/v1/accounts/{address}/transactions"
        params = {
            "only_to": "true",
            "limit": 100,
            "min_timestamp": min_timestamp,
            "order_by": "block_timestamp,asc"
        }
        
        try:
            resp = requests.get(url, params=params, headers=self._headers(), timeout=20)
            resp.raise_for_status()
            data = resp.json()

            if not data.get("success", False):
                raise TronGridError(str(data))

            # Фильтруем только нативные TRX переводы (не TRC20)
            native_transactions = []
            for tx in data.get("data", []):
                # Проверяем, что это обычный перевод TRX, а не TRC20
                contracts = tx.get("raw_data", {}).get("contract", [])
                if contracts and contracts[0].get("type") == "TransferContract":
                    native_transactions.append(tx)
                    
            return native_transactions

        except requests.RequestException as e:
            logger.error(f"Request to TronGrid failed for native TRX: {e}")
            raise TronGridError(f"TronGrid native TRX request failed: {e}")

    def send_transaction(self, private_key: str, to_address: str, amount: Decimal, memo: str = "", contract_address: str = None) -> str:
        """Sends TRC20 token or native TRX from a platform wallet to an external address."""
        logger.info(f"[TRON][SEND] Sending {amount} to {to_address} with memo '{memo}', contract: {contract_address}")
        priv_key = PrivateKey(bytes.fromhex(private_key))
        
        # Если contract_address пустой или None, отправляем нативный TRX
        if not contract_address or contract_address.strip() == "":
            return self._send_native_trx(priv_key, to_address, amount, memo)
        
        # Иначе отправляем TRC20 токен
        return self._send_trc20_token(priv_key, to_address, amount, memo, contract_address)

    def _send_trc20_token(self, priv_key, to_address: str, amount: Decimal, memo: str, contract_address: str) -> str:
        """Sends TRC20 token."""
        # Инициализируем контракт сразу с ABI
        contract = Contract(addr=contract_address, abi=json.loads(TRC20_ABI), client=self.client)
        
        # Получаем decimals из модели Cryptocurrency
        from crypto.models import Cryptocurrency
        try:
            currency = Cryptocurrency.objects.get(contract_address=contract_address)
            decimals = currency.decimals
        except Cryptocurrency.DoesNotExist:
            decimals = 6 # Default
            logger.warning(f"Could not find Cryptocurrency with contract {contract_address}, defaulting to {decimals} decimals.")

        amount_int = self.to_atomic_unit(amount, decimals)

        txn = (
            contract.functions.transfer(to_address, amount_int)
            .with_owner(priv_key.public_key.to_base58check_address())
            .fee_limit(5_000_000)
        )
        if memo:
            txn = txn.memo(memo)
        
        signed_txn = txn.build().sign(priv_key)
        
        try:
            result = signed_txn.broadcast().wait(timeout=30)
            logger.info(f"[TRON][SEND] TRC20 tx broadcasted and confirmed. Result: {result}")
            return result['id']
        except TimeoutError as e:
            logger.error(f"[TRON][SEND] Timeout waiting for TRC20 tx confirmation: {e}")
            raise TronGridError(f"TRC20 transaction wait timeout: {e}")
        except Exception as e:
            logger.error(f"[TRON][SEND] Error broadcasting or waiting for TRC20 tx: {e}")
            raise TronGridError(f"TRC20 transaction error: {e}")

    def _send_native_trx(self, priv_key, to_address: str, amount: Decimal, memo: str) -> str:
        """Sends native TRX."""
        amount_sun = self.to_atomic_unit(amount, 6)  # TRX имеет 6 decimals
        
        txn = (
            self.client.trx.transfer(priv_key.public_key.to_base58check_address(), to_address, amount_sun)
            .fee_limit(5_000_000)
        )
        if memo:
            txn = txn.memo(memo)
        
        signed_txn = txn.build().sign(priv_key)
        
        try:
            result = signed_txn.broadcast().wait(timeout=30)
            logger.info(f"[TRON][SEND] Native TRX tx broadcasted and confirmed. Result: {result}")
            return result['id']
        except TimeoutError as e:
            logger.error(f"[TRON][SEND] Timeout waiting for native TRX tx confirmation: {e}")
            raise TronGridError(f"Native TRX transaction wait timeout: {e}")
        except Exception as e:
            logger.error(f"[TRON][SEND] Error broadcasting or waiting for native TRX tx: {e}")
            raise TronGridError(f"Native TRX transaction error: {e}")

    def get_balance(self, address: str, contract_address: str = None) -> Decimal:
        """Gets the token balance or native TRX balance for a given address."""
        # Если contract_address не передан или пустой, то получаем нативный TRX баланс
        if not contract_address or contract_address.strip() == "":
            return self._get_native_trx_balance(address)
        
        # Иначе получаем баланс TRC20 токена
        return self._get_trc20_balance(address, contract_address)

    def _get_trc20_balance(self, address: str, contract_address: str) -> Decimal:
        """Gets TRC20 token balance."""
        # Получаем decimals из модели Cryptocurrency
        from crypto.models import Cryptocurrency
        try:
            currency = Cryptocurrency.objects.get(contract_address=contract_address)
            decimals = currency.decimals
        except Cryptocurrency.DoesNotExist:
            decimals = 6 # Default
            logger.warning(f"Could not find Cryptocurrency with contract {contract_address}, defaulting to {decimals} decimals.")
        
        contract = Contract(addr=contract_address, abi=json.loads(TRC20_ABI), client=self.client)
        balance_raw = contract.functions.balanceOf(address)
        return self.from_atomic_unit(balance_raw, decimals)

    def _get_native_trx_balance(self, address: str) -> Decimal:
        """Gets native TRX balance."""
        try:
            account_info = self.client.get_account(address)
            balance_sun = account_info.get('balance', 0)  # Баланс в SUN (1 TRX = 1,000,000 SUN)
            return self.from_atomic_unit(balance_sun, 6)  # TRX имеет 6 decimals
        except Exception as e:
            logger.error(f"Error getting native TRX balance for {address}: {e}")
            return Decimal('0')

    def create_new_address(self, user_id: int, **kwargs) -> Tuple[str, str]:
        """Creates a new Tron address and private key for a user using HD generation."""
        try:
            master_seed_hex = getattr(settings, 'TRON_MASTER_SEED_HEX', None)
            if not master_seed_hex:
                raise ValueError("TRON_MASTER_SEED_HEX is not configured in settings.")

            seed_bytes = bytes.fromhex(master_seed_hex)
            
            bip44_mst = Bip44.FromSeed(seed_bytes, self.bip44_coin)
            
            # Используем timestamp для генерации уникальных адресов при ротации
            import time
            timestamp_index = int(time.time()) % 1000000  # Последние 6 цифр timestamp для уникальности
            unique_index = (user_id * 1000000) + timestamp_index  # Комбинируем user_id с timestamp
            
            # Path: m/44'/195'/0'/0/<unique_index>
            bip44_acc = bip44_mst.Purpose().Coin().Account(0)
            bip44_chg = bip44_acc.Change(Bip44Changes.CHAIN_EXT)
            bip44_addr = bip44_chg.AddressIndex(unique_index)

            address = bip44_addr.PublicKey().ToAddress()
            private_key_hex = bip44_addr.PrivateKey().Raw().ToHex()
            
            logger.info(f"Generated new Tron address for user {user_id} (index {unique_index}): {address}")
            return address, private_key_hex
            
        except Exception as e:
            logger.error(f"Error creating HD Tron address for user {user_id}: {e}", exc_info=True)
            raise Exception(f"Failed to create HD Tron address: {e}")

    def is_transaction_confirmed(self, tx_hash: str) -> bool:
        """
        Checks if a transaction is confirmed on the Tron blockchain.
        
        :param tx_hash: Transaction hash to check.
        :return: True if confirmed, False otherwise.
        """
        try:
            tx_data = self._get_transaction_by_id(tx_hash)
        except Exception as e:
            # Если RPC недоступен, НЕ считаем это ошибкой транзакции
            logger.warning(f"[TRON][CONFIRM] RPC error checking {tx_hash}: {e}. Will retry later.")
            raise e  # Передаем ошибку наверх для retry
            
        try:
            logger.info(f"[TRON][CONFIRM][DEBUG] Received tx_data for {tx_hash}: {tx_data}")
            
            # Проверяем наличие ключей в ответе
            if not tx_data:
                logger.warning(f"[TRON][CONFIRM] Empty transaction data for {tx_hash}")
                return False
            
            # Проверяем статус транзакции
            # В Tron, если транзакция успешно подтверждена, то поле ret[0].contractRet будет равно "SUCCESS"
            # Также транзакция считается подтвержденной, если она включена в блок (blockNumber существует)
            ret_data = tx_data.get("ret")
            logger.info(f"[TRON][CONFIRM][DEBUG] ret_data: {ret_data}")
            if ret_data:
                first_ret = ret_data[0] if ret_data else {}
                logger.info(f"[TRON][CONFIRM][DEBUG] first_ret: {first_ret}")
                contract_ret = first_ret.get("contractRet")
                logger.info(f"[TRON][CONFIRM][DEBUG] contractRet: '{contract_ret}'")
                if contract_ret == "SUCCESS":
                    logger.info(f"[TRON][CONFIRM] Transaction {tx_hash} is confirmed by contractRet.")
                    return True
                else:
                    logger.info(f"[TRON][CONFIRM] Transaction {tx_hash} is not yet confirmed. contractRet: '{contract_ret}'")
                    return False
            else:
                # Если поле 'ret' отсутствует, проверяем наличие 'blockNumber'
                block_number = tx_data.get("blockNumber")
                logger.info(f"[TRON][CONFIRM][DEBUG] blockNumber: {block_number}")
                if block_number:
                    logger.info(f"[TRON][CONFIRM] Transaction {tx_hash} is confirmed by blockNumber.")
                    return True
                else:
                    logger.info(f"[TRON][CONFIRM] Transaction {tx_hash} is not yet confirmed. No blockNumber.")
                    return False
            
        except TronGridError as e:
            logger.error(f"[TRON][CONFIRM] TronGridError for tx {tx_hash}: {e}")
            # Считаем, что транзакция не подтверждена, если произошла ошибка
            return False
        except Exception as e:
            logger.error(f"[TRON][CONFIRM] Unexpected error for tx {tx_hash}: {e}", exc_info=True)
            # Считаем, что транзакция не подтверждена, если произошла ошибка
            return False
