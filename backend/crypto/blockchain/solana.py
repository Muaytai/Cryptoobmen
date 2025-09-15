from decimal import Decimal
from typing import List, Dict, Any
import logging
import os

import json
import base58
from typing import Union

from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction import VersionedTransaction
from solders.system_program import TransferParams, transfer
from solders.message import Message
from solders.message import MessageV0

# Если нужно использовать memo
# from spl.memo.instructions import encode_memo

from .base import BaseBlockchainService

logger = logging.getLogger(__name__)

# Получаем API ключ из переменной окружения
HELIUS_API_KEY = os.getenv('HELIUS_API_KEY', '97e0bbe6-80d0-466d-88bc-049811db2bfb')

RPC_ENDPOINTS = {
    "mainnet": "https://api.mainnet-beta.solana.com",
    "testnet": "https://api.testnet.solana.com",
    "devnet": f"https://devnet.helius-rpc.com/?api-key={HELIUS_API_KEY}",
}


from solana.rpc.types import TxOpts
from typing import Optional
from requests.exceptions import Timeout, ConnectionError
from solana.rpc.core import RPCException

class SolanaService(BaseBlockchainService):
    def __init__(self, network: str = "devnet"):
        super().__init__(network)
        if network not in RPC_ENDPOINTS:
            raise ValueError("Network must be 'mainnet', 'testnet' or 'devnet'")

        # Установите таймауты: connect=10s, read=15s
        self.client = Client(
            RPC_ENDPOINTS[network],
            timeout=15,  # seconds
        )
        logger.info(f"SolanaService initialized with network: {network}, RPC: {RPC_ENDPOINTS[network]}")

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

    def send_transaction(self, private_key_input: str, to_address: str, amount: Decimal, memo: str = "") -> str:
        try:
            secret_key_bytes = self._parse_private_key(private_key_input)
            sender = Keypair.from_bytes(secret_key_bytes)
            recipient = Pubkey.from_string(to_address)
            lamports = int(amount * 1_000_000_000)

            # Получаем blockhash один раз
            try:
                recent_blockhash_resp = self.client.get_latest_blockhash()
                recent_blockhash = recent_blockhash_resp.value.blockhash
            except (Timeout, ConnectionError, RPCException) as e:
                logger.error(f"[send_transaction] Не удалось получить blockhash: {e}")
                raise Exception("RPC timeout: не удалось подключиться к Solana сети")

            # 1. Создаём инструкцию
            transfer_instruction = transfer(
                TransferParams(
                    from_pubkey=sender.pubkey(),
                    to_pubkey=recipient,
                    lamports=lamports
                )
            )


            # # 2. Собираем message (позиционно!)
            # message = Message.new_with_blockhash(
            #     [transfer_instruction],  # ✅ Список инструкций
            #     sender.pubkey(),  # ✅ Payer
            #     recent_blockhash  # ✅ Blockhash
            # )

            # 2. Собираем message
            message = MessageV0.try_compile(
                payer=sender.pubkey(),
                instructions=[transfer_instruction],
                address_lookup_table_accounts=[],
                recent_blockhash=recent_blockhash
            )

            # 3. Создаём транзакцию и подписываем
            # txn = txn = Transaction(message=message, recent_blockhash=recent_blockhash, from_keypairs=sender.pubkey())
            # txn.sign(*[sender])  # Подписываем приватным ключом отправителя

            transaction = VersionedTransaction(message, [sender])

            # Отправляем
            try:
                response = self.client.send_transaction(transaction)
                tx_hash = str(response.value)
                logger.info(f"[send_transaction] Успешно отправлено: {tx_hash}")
                return tx_hash
            except (Timeout, ConnectionError) as e:
                logger.error(f"[send_transaction] Отправка транзакции не удалась: {e}")
                raise Exception("Таймаут при отправке транзакции")

        except Exception as e:
            logger.error(f"[send_transaction] Ошибка: {e}", exc_info=True)
            raise

    def _parse_private_key(self, key_str: str) -> bytes:
        """
        Парсит приватный ключ из hex, JSON-массива или base58.
        Возвращает 64-байтный массив.
        """
        key_str = key_str.strip()

        # Вариант 1: JSON-массив чисел, например: [251, 34, ..., 123]
        if key_str.startswith('[') and key_str.endswith(']'):
            try:
                secret_key = json.loads(key_str)
                if isinstance(secret_key, list) and all(isinstance(i, int) for i in secret_key):
                    return bytes(secret_key)
            except json.JSONDecodeError:
                raise ValueError("Неверный формат JSON-ключа")

        # Вариант 2: Hex-строка (128 hex-символов)
        if len(key_str) == 128 and all(c in '0123456789abcdefABCDEF' for c in key_str):
            try:
                return bytes.fromhex(key_str)
            except ValueError:
                raise ValueError("Неверная hex-строка")

        if key_str.startswith('0x') and len(key_str) == 130:
            try:
                return bytes.fromhex(key_str[2:])
            except ValueError:
                raise ValueError("Неверная hex-строка после 0x")

        # Вариант 3: Base58 (редко, но возможно)
        try:
            decoded = base58.b58decode(key_str)
            if len(decoded) == 64:
                return decoded
        except Exception:
            pass

        raise ValueError("Не удалось распознать формат приватного ключа. Ожидался hex, JSON-массив или base58.")

    def create_new_address(self, user_id: int = None) -> str:
        """Создает новый адрес Solana"""
        try:
            # Генерируем новую пару ключей
            keypair = Keypair()
            public_address = str(keypair.pubkey())
            private_key_bytes = bytes(keypair.secret())

            logger.info(f"Создан новый адрес Solana: {public_address}")
            return public_address

        except Exception as e:
            logger.error(f"[create_new_address] Failed to create SOL address: {e}")
            raise ValueError(f"Не удалось создать новый адрес Solana: {e}")