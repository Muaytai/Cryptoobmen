"""Service for interacting with the Tron blockchain (TRC20 tokens)."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import List, Dict, Any
import json
from decimal import Decimal

import requests
from tronpy import Tron
from tronpy.keys import PrivateKey
from django.conf import settings

from .base import BaseBlockchainService

logger = logging.getLogger(__name__)

# Contract address for USDT on TRON (TRC20) - Nile Testnet
USDT_CONTRACT = settings.USDT_TRC20_CONTRACT_ADDRESS

class TronGridError(RuntimeError):
    """Raised when TronGrid returns an error."""

class TronService(BaseBlockchainService):
    """
    Service for interacting with the Tron blockchain.
    Implements the BaseBlockchainService interface.
    """

    def __init__(self, network: str = 'nile'):
        super().__init__(network)
        self.client = Tron(network=self.network)
        self.api_url = settings.TRON_API_URL
        self.api_key = settings.TRONGRID_API_KEY

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

    def get_transactions(self, address: str, min_timestamp: int = 0) -> List[Dict[str, Any]]:
        """Fetches TRC20 transfers to *address* after *min_timestamp* (ms)."""
        # Базовая проверка валидности адреса Tron
        if not address or not address.startswith('T') or len(address) != 34:
            logger.warning(f"[TRON] Пропуск невалидного адреса: {address}")
            return []

        url = f"{self.api_url}/v1/accounts/{address}/transactions/trc20"
        params = {
            "only_to": "true",
            "limit": 100,
            "min_timestamp": min_timestamp,
            "contract_address": USDT_CONTRACT,
            "order_by": "block_timestamp,asc"
        }
        
        try:
            resp = requests.get(url, params=params, headers=self._headers(), timeout=20)
            logger.info(f"[TRON][RAW_RESPONSE] {resp.text}")
            resp.raise_for_status()
            data = resp.json()

            if not data.get("success", False):
                raise TronGridError(str(data))

            transfers_with_memo = []
            for item in data.get("data", []):
                tx_id = item.get("transaction_id")
                if not tx_id:
                    continue
                
                memo = ""
                try:
                    tx_info = self._get_transaction_by_id(tx_id)
                    if tx_info.get("raw_data", {}).get("data"):
                        raw_data = tx_info["raw_data"]["data"]
                        memo = bytes.fromhex(raw_data).decode('utf-8', 'ignore').strip()
                except Exception:
                    pass  # Ignore errors in getting memo

                item['memo'] = "".join(filter(str.isprintable, memo)).strip()
                transfers_with_memo.append(item)
                
            return transfers_with_memo

        except requests.RequestException as e:
            logger.error(f"Request to TronGrid failed: {e}")
            raise TronGridError(f"TronGrid request failed: {e}")

    def send_transaction(self, private_key: str, to_address: str, amount: Decimal, memo: str = "") -> str:
        """Sends USDT (TRC20) from a platform wallet to an external address."""
        priv_key = PrivateKey(bytes.fromhex(private_key))
        contract = self.client.get_contract(USDT_CONTRACT)
        
        # USDT has 6 decimals
        amount_int = self.to_atomic_unit(amount, 6)

        txn = (
            contract.functions.transfer(to_address, amount_int)
            .with_owner(priv_key.public_key.to_base58check_address())
            .fee_limit(5_000_000)
        )
        if memo:
            txn = txn.memo(memo)
        
        signed_txn = txn.build().sign(priv_key)
        result = signed_txn.broadcast().wait()
        return result['id']

    def get_balance(self, address: str) -> Decimal:
        """Gets the USDT balance for a given address."""
        contract = self.client.get_contract(USDT_CONTRACT)
        balance_raw = contract.functions.balanceOf(address)
        # USDT has 6 decimals
        return self.from_atomic_unit(balance_raw, 6)

    def create_new_address(self, *args, **kwargs):
        """Creates a new Tron address."""
        try:
            # This is not a secure way to generate keys for production.
            # For demonstration purposes only.
            priv_key = PrivateKey.random()
            address = priv_key.public_key.to_base58check_address()
            return address
        except Exception as e:
            logger.error(f"Error creating new Tron address: {e}")
            raise
