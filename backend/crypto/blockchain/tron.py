"""Utility functions for interacting with TronGrid API (TRC20 deposits)."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import List, Dict, Any
import json

import requests
from tronpy import Tron
from tronpy.keys import PrivateKey

logger = logging.getLogger(__name__)

TRONGRID_API_KEY = os.getenv("TRONGRID_API_KEY")
TRONGRID_API_URL = os.getenv("TRON_API_URL", "https://nile.trongrid.io")
# Contract address for USDT on TRON (TRC20) - Nile Testnet
USDT_CONTRACT = "TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf" # Updated to Nile Testnet USDT contract address


class TronGridError(RuntimeError):
    """Raised when TronGrid returns an error."""


def _headers() -> Dict[str, str]:
    headers = {
        "Accept": "application/json",
    }
    if TRONGRID_API_KEY:
        headers["TRON-PRO-API-KEY"] = TRONGRID_API_KEY
    
    # Логирование заголовков для отладки
    logger.info(f"[_headers] Using headers: {json.dumps(headers, indent=2)}")
    return headers


# New helper function to get full transaction info by ID
def _get_transaction_by_id(tx_id: str) -> Dict[str, Any]:
    url = f"{TRONGRID_API_URL}/wallet/gettransactionbyid"
    payload = {
        "value": tx_id
    }
    logger.info(f"[_get_transaction_by_id] Making request to {url} with payload: {json.dumps(payload, indent=2)}")
    
    try:
        resp = requests.post(url, json=payload, headers=_headers(), timeout=10)
        logger.info(f"[_get_transaction_by_id] Response status code: {resp.status_code}")
        
        if resp.status_code != 200:
            logger.error(f"[_get_transaction_by_id] TronGrid HTTP error {resp.status_code}: {resp.text}")
            raise TronGridError(f"TronGrid HTTP {resp.status_code}: {resp.text}")
            
        data = resp.json()
        logger.info(f"[_get_transaction_by_id] Raw TronGrid transaction info response for {tx_id}: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        logger.exception(f"[_get_transaction_by_id] Unexpected error for tx_id {tx_id}: {e}")
        raise


def get_trc20_transfers(address: str, min_timestamp: int) -> List[Dict[str, Any]]:
    """Fetches TRC20 transfers to *address* after *min_timestamp* (ms).

    Args:
        address: TRON address (base58).
        min_timestamp: minimal block timestamp (milliseconds since epoch).

    Returns:
        List of raw transfer dicts (TronGrid format).
    """
    url = f"{TRONGRID_API_URL}/v1/accounts/{address}/transactions/trc20"
    params = {
        "only_to": "true",
        "limit": 100,
        "min_timestamp": min_timestamp,
        "contract_address": USDT_CONTRACT,
        "order_by": "block_timestamp,asc"
    }
    
    try:
        resp = requests.get(url, params=params, headers=_headers(), timeout=20)
        
        if resp.status_code != 200:
            logger.error(f"TronGrid HTTP error {resp.status_code}: {resp.text}")
            raise TronGridError(f"TronGrid HTTP {resp.status_code}: {resp.text}")
            
        data = resp.json()
        
        if not data.get("success", False):
            logger.error(f"TronGrid API error: {data}")
            raise TronGridError(str(data))

        transfers_with_memo = []
        for item in data.get("data", []):
            tx_id = item.get("transaction_id")
            if not tx_id:
                continue
                
            memo = ""
            try:
                tx_info = _get_transaction_by_id(tx_id)
                if not tx_info:
                    logger.warning(f"[get_trc20_transfers] No tx_info for {tx_id}, skipping.")
                    continue
                    
                if tx_info.get("raw_data", {}).get("data"):
                    try:
                        raw_data = tx_info["raw_data"]["data"]
                        if raw_data:
                            memo = bytes.fromhex(raw_data).decode('utf-8', errors='ignore').strip()
                            logger.info(f"[get_trc20_transfers] Found memo '{memo}' in tx {tx_id}")
                    except (ValueError, AttributeError, KeyError) as e:
                        logger.warning(f"[get_trc20_transfers] Could not decode memo from {raw_data} for tx {tx_id}: {e}")
                        pass
                else:
                    logger.info(f"[get_trc20_transfers] No 'data' field in raw_data for tx {tx_id}. No memo.")

            except Exception as e:
                logger.error(f"[get_trc20_transfers] Error fetching/parsing tx_info for {tx_id}: {e}", exc_info=True)
                pass # Continue to next transaction even if one fails

            # ВСЕГДА добавляем транзакцию, даже если memo пустой.
            # На этапе extract_deposit_events будем решать, что с ней делать.
            cleaned_memo = "".join(filter(str.isprintable, memo)).strip()
            item['memo'] = cleaned_memo # Добавляем memo (даже если пустой) в item
            transfers_with_memo.append(item)
            
        logger.info(f"[get_trc20_transfers] Total transfers processed (with and without memo): {len(transfers_with_memo)}")
        return transfers_with_memo

    except requests.Timeout:
        logger.error("Request to TronGrid timed out")
        raise TronGridError("TronGrid request timed out")
    except requests.RequestException as e:
        logger.error(f"Request to TronGrid failed: {e}")
        raise TronGridError(f"TronGrid request failed: {e}")


def extract_deposit_events(transfers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Converts raw transfers to simplified deposit events."""
    events: List[Dict[str, Any]] = []
    for item in transfers:
        # Expect following keys: "to", "value", "block_timestamp", "transaction_id", "token_info", "type", "from", "memo"
        memo = item.get("memo") or "" # Memo will now be present in the item directly
        if not memo:
            logger.info(f"[extract_deposit_events] Skipping transaction {item.get('transaction_id')} due to empty memo.") # Added logging
            continue # требуется Memo для связи с пользователем
        value_raw = int(item["value"])
        decimals = int(item["token_info"].get("decimals", 6))
        amount = value_raw / (10 ** decimals)
        events.append({
            "tx_hash": item["transaction_id"],
            "amount": amount,
            "memo": memo,
            "timestamp": datetime.fromtimestamp(item["block_timestamp"] / 1000, tz=timezone.utc).isoformat(),
        })
    logger.info(f"[extract_deposit_events] Extracted events: {json.dumps(events, indent=2)}")
    return events


def send_usdt_trc20(from_priv_key: str, to_address: str, amount: float, memo: str = "") -> str:
    """
    Отправляет USDT (TRC20) с платформенного кошелька на внешний адрес через tronpy.
    :param from_priv_key: приватный ключ отправителя (hex-строка)
    :param to_address: TRON адрес получателя (base58)
    :param amount: сумма в USDT (десятичное число)
    :param memo: опционально, memo для транзакции
    :return: tx_hash (str)
    """
    client = Tron(network='nile')  # или mainnet
    priv_key = PrivateKey(bytes.fromhex(from_priv_key))
    contract = client.get_contract(USDT_CONTRACT)
    # USDT имеет 6 знаков после запятой
    amount_int = int(amount * 1_000_000)
    txn = (
        contract.functions.transfer(to_address, amount_int)
        .with_owner(priv_key.public_key.to_base58check_address())
        .fee_limit(5_000_000)
    )
    if memo:
        txn = txn.memo(memo)
    txn = txn.build().sign(priv_key)
    result = txn.broadcast().wait()
    return result['id']
