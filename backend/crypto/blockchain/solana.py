from decimal import Decimal
from typing import List, Dict, Any
import logging

from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.system_program import TransferParams, transfer

# Если нужно использовать memo
# from spl.memo.instructions import encode_memo

from .base import BaseBlockchainService

logger = logging.getLogger(__name__)

RPC_ENDPOINTS = {
    "mainnet": "https://api.mainnet-beta.solana.com",
    "testnet": "https://api.testnet.solana.com",
    "devnet": "https://devnet.helius-rpc.com/?api-key=97e0bbe6-80d0-466d-88bc-049811db2bfb",
}


class SolanaService(BaseBlockchainService):
    def __init__(self, network: str = "devnet"):
        super().__init__(network)
        if network not in RPC_ENDPOINTS:
            raise ValueError("Network must be 'mainnet', 'testnet' or 'devnet'")
        self.client = Client(RPC_ENDPOINTS[network])
        logger.info(f"SolanaService initialized with network: {network}")

    def get_transactions(self, address: str, min_timestamp: int = 0) -> List[Dict[str, Any]]:
        try:
            pubkey = Pubkey.from_string(address)
            signatures = self.client.get_signatures_for_address(pubkey, limit=20).value
            if not signatures:
                return []

            transactions = []
            for sig_info in signatures:
                tx_resp = self.client.get_transaction(sig_info.signature).value
                if tx_resp is None:
                    continue

                # block_time
                block_time = getattr(tx_resp, "block_time", None)
                if block_time is not None and hasattr(block_time, "value"):
                    block_time = block_time.value  # если Some(...)
                if min_timestamp and block_time and block_time < min_timestamp // 1000:
                    continue

                # transaction_with_meta
                transaction_with_meta = getattr(tx_resp, "transaction", None)
                if transaction_with_meta is None:
                    continue

                # meta
                meta = getattr(transaction_with_meta, "meta", None)
                if meta is not None and hasattr(meta, "value"):
                    meta = meta.value  # если Some(...)
                if meta is None:
                    continue

                # transaction (UiTransaction)
                tx_json = getattr(transaction_with_meta, "transaction", None)
                if tx_json is not None and hasattr(tx_json, "value"):
                    tx_json = tx_json.value  # если Json(...)
                if tx_json is None:
                    continue

                # message
                message = getattr(tx_json, "message", None)
                if message is not None and hasattr(message, "value"):
                    message = message.value  # если Raw(...)
                if message is None:
                    continue

                account_keys = getattr(message, "account_keys", [])
                pre_balances = getattr(meta, "pre_balances", [])
                post_balances = getattr(meta, "post_balances", [])

                for i, acc in enumerate(account_keys):
                    if str(acc) == address:
                        diff = post_balances[i] - pre_balances[i]
                        if diff > 0:
                            transactions.append({
                                "transaction_id": str(sig_info.signature),
                                "from_address": str(account_keys[0]),
                                "to_address": address,
                                "value": str(diff),
                                "memo": None
                            })
            return transactions

        except Exception as e:
            logger.error(f"[get_transactions] Error for {address}: {e}")
            return []

    def get_balance(self, address: str) -> Decimal:
        try:
            pubkey = Pubkey.from_string(address)
            balance_resp = self.client.get_balance(pubkey)
            lamports = balance_resp.value
            return self.from_atomic_unit(lamports, 9)
        except Exception as e:
            logger.error(f"[get_balance] Error for {address}: {e}")
            return Decimal("0.0")

    def send_transaction(self, private_key_hex: str, to_address: str, amount: Decimal, memo: str = "") -> str:
        try:
            # Преобразуем приватный ключ из hex в байты
            secret_key_bytes = bytes.fromhex(private_key_hex)
            if len(secret_key_bytes) != 64:
                raise ValueError("Private key must be 64-byte hex string")

            sender = Keypair.from_bytes(secret_key_bytes)
            recipient = Pubkey.from_string(to_address)
            lamports = self.to_atomic_unit(amount, 9)

            txn = Transaction()
            txn.add(transfer(TransferParams(from_pubkey=sender.pubkey(), to_pubkey=recipient, lamports=lamports)))

            # Добавление memo (если нужно и используете Memo Program)
            # if memo:
            #     txn.add(encode_memo(memo))

            response = self.client.send_transaction(txn, sender)
            return response.value  # transaction signature
        except Exception as e:
            logger.error(f"[send_transaction] Failed to send SOL: {e}")
            raise

    def create_new_address(self):
        # Временная заглушка
        pass