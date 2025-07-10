"""Utility functions for interacting with Solana blockchain (SPL USDT deposits)."""
import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from solana.rpc.api import Client
import requests

logger = logging.getLogger(__name__)

# Solana RPC URL (можно использовать https://api.mainnet-beta.solana.com или свой)
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
# SPL USDT contract address (mint address)
SPL_USDT_MINT = os.getenv("SPL_USDT_MINT", "Es9vMFrzaCERk8f2F3h8zGzQ6rQ5o6Q1rS4Q1Q1Q1Q1Q")  # Mainnet USDT

class SolanaError(RuntimeError):
    """Raised when Solana API returns an error."""


def get_spl_usdt_transfers(address: str, min_slot: int = 0) -> List[Dict[str, Any]]:
    """
    Получает входящие SPL USDT транзакции на адрес после указанного слота.
    Args:
        address: Solana address (str)
        min_slot: минимальный слот (int)
    Returns:
        List of dicts с информацией о переводах
    """
    client = Client(SOLANA_RPC_URL)
    # Получаем список токен-аккаунтов для адреса
    resp = client.get_token_accounts_by_owner(address, {'mint': SPL_USDT_MINT})
    if not resp["result"] or not resp["result"]["value"]:
        logger.info(f"[get_spl_usdt_transfers] Нет токен-аккаунтов USDT для {address}")
        return []
    token_accounts = [acc["pubkey"] for acc in resp["result"]["value"]]
    transfers = []
    for token_acc in token_accounts:
        # Получаем историю транзакций для токен-аккаунта
        txs = client.get_signatures_for_address(token_acc, limit=50)
        for tx in txs["result"]:
            if min_slot and tx["slot"] < min_slot:
                continue
            # Получаем детали транзакции
            tx_detail = client.get_transaction(tx["signature"], encoding="json")
            if not tx_detail["result"]:
                continue
            meta = tx_detail["result"]["meta"]
            if not meta or not meta.get("postTokenBalances"):
                continue
            # Ищем входящие переводы USDT
            for bal in meta["postTokenBalances"]:
                if bal["mint"] == SPL_USDT_MINT and bal["owner"] == address:
                    pre_bal = next((b for b in meta["preTokenBalances"] if b["accountIndex"] == bal["accountIndex"]), None)
                    pre_amt = int(pre_bal["uiTokenAmount"]["amount"]) if pre_bal else 0
                    post_amt = int(bal["uiTokenAmount"]["amount"])
                    delta = post_amt - pre_amt
                    if delta > 0:
                        transfers.append({
                            "signature": tx["signature"],
                            "amount": delta / (10 ** int(bal["uiTokenAmount"]["decimals"])),
                            "slot": tx["slot"],
                            "block_time": tx.get("blockTime"),
                            "memo": None,  # В Solana можно использовать memo-инструкцию, если нужно
                        })
    logger.info(f"[get_spl_usdt_transfers] Найдено {len(transfers)} входящих переводов USDT для {address}")
    return transfers


def extract_deposit_events(transfers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Преобразует сырые переводы в события депозитов."""
    events = []
    for item in transfers:
        # Memo можно реализовать через отдельную инструкцию Memo в транзакции
        memo = item.get("memo") or ""
        # Если требуется, можно фильтровать только с memo
        # if not memo:
        #     continue
        events.append({
            "tx_hash": item["signature"],
            "amount": item["amount"],
            "memo": memo,
            "timestamp": datetime.fromtimestamp(item["block_time"], tz=timezone.utc).isoformat() if item.get("block_time") else None,
        })
    logger.info(f"[extract_deposit_events] Extracted events: {events}")
    return events 