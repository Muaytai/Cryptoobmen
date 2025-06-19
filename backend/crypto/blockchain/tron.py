"""Utility functions for interacting with TronGrid API (TRC20 deposits)."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import List, Dict, Any
import json

import requests

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
    return headers


# New helper function to get full transaction info by ID
def _get_transaction_by_id(tx_id: str) -> Dict[str, Any]:
    url = f"{TRONGRID_API_URL}/wallet/gettransactionbyid"
    payload = {
        "value": tx_id
    }
    resp = requests.post(url, json=payload, headers=_headers(), timeout=10)
    if resp.status_code != 200:
        logger.error(f"[_get_transaction_by_id] TronGrid HTTP error {resp.status_code}: {resp.text}")
        raise TronGridError(f"TronGrid HTTP {resp.status_code}: {resp.text}")
    data = resp.json()
    logger.info(f"[_get_transaction_by_id] Raw TronGrid transaction info response for {tx_id}: {json.dumps(data, indent=2)}")
    return data


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
        "limit": 50,
        "min_timestamp": min_timestamp,
        "contract_address": USDT_CONTRACT,
        "order_by": "block_timestamp,asc",
    }
    resp = requests.get(url, params=params, headers=_headers(), timeout=10)
    if resp.status_code != 200:
        logger.error(f"[get_trc20_transfers] TronGrid HTTP error {resp.status_code}: {resp.text}")
        raise TronGridError(f"TronGrid HTTP {resp.status_code}: {resp.text}")
    data = resp.json()
    logger.info(f"[get_trc20_transfers] Raw TronGrid response: {json.dumps(data, indent=2)}")
    if not data.get("success", False):
        logger.error(f"[get_trc20_transfers] TronGrid API error: {data}")
        raise TronGridError(str(data))

    # Fetch memo for each transaction
    transfers_with_memo = []
    for item in data.get("data", []):
        tx_id = item.get("transaction_id")
        if tx_id:
            memo = ""
            try:
                tx_info = _get_transaction_by_id(tx_id)
                logger.info(f"[get_trc20_transfers] Full tx_info for {tx_id}: {json.dumps(tx_info, indent=2)}")

                # Try to extract memo from raw_data.contract[0].parameter.value.data
                if "raw_data" in tx_info and isinstance(tx_info["raw_data"], dict) and \
                   "contract" in tx_info["raw_data"] and isinstance(tx_info["raw_data"]["contract"], list) and \
                   len(tx_info["raw_data"]["contract"]) > 0 and \
                   "parameter" in tx_info["raw_data"]["contract"][0] and isinstance(tx_info["raw_data"]["contract"][0]["parameter"], dict) and \
                   "value" in tx_info["raw_data"]["contract"][0]["parameter"] and isinstance(tx_info["raw_data"]["contract"][0]["parameter"]["value"], dict) and \
                   "data" in tx_info["raw_data"]["contract"][0]["parameter"]["value"] and isinstance(tx_info["raw_data"]["contract"][0]["parameter"]["value"]["data"], str):
                    try:
                        memo = bytes.fromhex(tx_info["raw_data"]["contract"][0]["parameter"]["value"]["data"]).decode('utf-8').strip()
                        logger.info(f"[get_trc20_transfers] Found memo in 'raw_data.contract[0].parameter.value.data' (decoded hex) for {tx_id}: '{memo}'")
                    except ValueError:
                        logger.warning(f"[get_trc20_transfers] Could not decode hex memo from raw_data.contract for {tx_id}.")

                # If memo is still empty, try raw_data.data directly
                if not memo and "raw_data" in tx_info and isinstance(tx_info["raw_data"], dict) and \
                   "data" in tx_info["raw_data"] and isinstance(tx_info["raw_data"]["data"], str):
                    try:
                        raw_data_memo = bytes.fromhex(tx_info["raw_data"]["data"]).decode('utf-8').strip()
                        if raw_data_memo:
                            memo = raw_data_memo
                            logger.info(f"[get_trc20_transfers] Found memo in 'raw_data.data' (decoded hex) for {tx_id}: '{memo}'")
                    except ValueError:
                        logger.warning(f"[get_trc20_transfers] Could not decode hex memo from raw_data.data for {tx_id}.")

                # Fallback checks (less likely for TRC20 memo but kept for robustness)
                if not memo and "note" in tx_info and isinstance(tx_info["note"], str):
                    memo = tx_info["note"].strip()
                    logger.info(f"[get_trc20_transfers] Found memo in 'note' for {tx_id}: '{memo}'")

                if not memo and "resMessage" in tx_info and isinstance(tx_info["resMessage"], str):
                    try:
                        decoded_res_msg = bytes.fromhex(tx_info["resMessage"]).decode('utf-8').strip()
                        if decoded_res_msg:
                            memo = decoded_res_msg
                            logger.info(f"[get_trc20_transfers] Found memo in 'resMessage' (decoded hex) for {tx_id}: '{memo}'")
                        else:
                            memo = tx_info["resMessage"].strip()
                            logger.info(f"[get_trc20_transfers] Found memo in 'resMessage' (as is) for {tx_id}: '{memo}'")

                    except ValueError:
                        memo = tx_info["resMessage"].strip()
                        logger.info(f"[get_trc20_transfers] Found memo in 'resMessage' (not hex) for {tx_id}: '{memo}'")

                if not memo and "log" in tx_info and isinstance(tx_info["log"], list):
                    for log_entry in tx_info["log"]:
                        if "data" in log_entry and isinstance(log_entry["data"], str):
                            try:
                                decoded_log_data = bytes.fromhex(log_entry["data"]).decode('utf-8', errors='ignore').strip()
                                if decoded_log_data and all(32 <= ord(char) <= 126 for char in decoded_log_data): # Check for printable characters
                                    memo = decoded_log_data
                                    logger.info(f"[get_trc20_transfers] Found memo in 'log.data' (decoded hex, printable) for {tx_id}: '{memo}'")
                                    break
                            except ValueError:
                                pass # Not hex, continue

                # Clean the memo from null bytes and other non-printable characters
                if memo:
                    memo = ''.join(char for char in memo if 32 <= ord(char) <= 126) # Keep only printable ASCII characters
                    memo = memo.replace('\x00', '') # Remove null bytes (redundant after above line, but safe)
                logger.info(f"[get_trc20_transfers] Final extracted memo for {tx_id}: '{memo}'")
                item["memo"] = memo

            except TronGridError as e:
                logger.warning(f"[get_trc20_transfers] Could not fetch transaction info for {tx_id}: {e}")
                item["memo"] = "" # Ensure memo is empty if an error occurs during fetching
            except Exception as e:
                logger.error(f"[get_trc20_transfers] Unexpected error fetching transaction info for {tx_id}: {e}")
                item["memo"] = "" # Ensure memo is empty if an error occurs

        transfers_with_memo.append(item)

    return transfers_with_memo


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
