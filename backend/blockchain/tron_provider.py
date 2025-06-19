"""Провайдер для сети Tron (Nile/Mainnet).

Использует библиотеку `tronpy` для работы с RPC.
Работает с базовыми единицами «sun» (1 TRX = 1_000_000 sun).
Для TRC-20 токенов требуется адрес контракта и 6-18 десятичных знаков —
это передаётся как `contract_address`.

При необходимости URL узла и сеть можно переопределить через переменные
окружения TRON_NODE_URL, TRON_NETWORK (nile/mainnet).
"""
from __future__ import annotations

import os
from typing import Any, Dict

from tronpy import Tron
from tronpy.exceptions import TransactionError
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider

from .base import BlockchainProvider, DepositCallback

TRON_NETWORK = os.getenv("TRON_NETWORK", "nile")  # nile | mainnet
NODE_URL = os.getenv(
    "TRON_NODE_URL",
    "https://api.nile.trongrid.io" if TRON_NETWORK == "nile" else "https://api.trongrid.io",
)


class TronProvider(BlockchainProvider):
    """Минимальная реализация методов для приема/отправки TRX и TRC20."""

    network = f"Tron-{TRON_NETWORK}"

    def __init__(self) -> None:
        self.client = Tron(provider=HTTPProvider(NODE_URL))

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------
    def generate_address(self, user_id: int | str) -> dict[str, str]:
        priv_key = PrivateKey.random()
        return {"address": priv_key.public_key.to_base58check_address(), "private_key": priv_key.hex()}

    def get_balance(self, address: str, contract_address: str | None = None) -> int:
        if contract_address:
            # TRC20 — вызываем метод balanceOf(address)
            contract = self.client.get_contract(contract_address)
            return int(contract.functions.balanceOf(address))
        return int(self.client.get_account_balance(address) * 1_000_000)  # TRX -> sun

    def send_tx(
        self,
        priv_key_hex: str,
        to_address: str,
        amount: int,
        contract_address: str | None = None,
    ) -> str:
        pk = PrivateKey(bytes.fromhex(priv_key_hex))
        owner_address = pk.public_key.to_base58check_address()

        if contract_address:
            # TRC20 transfer(address,uint256)
            contract = self.client.get_contract(contract_address)
            txn = (
                contract.functions.transfer(to_address, amount)
                .with_owner(owner_address)
                .fee_limit(2_000_000)
                .build()
                .sign(pk)
                .broadcast()
            )
        else:
            # native TRX
            txn = (
                self.client.trx.transfer(owner_address, to_address, amount)
                .build()
                .sign(pk)
                .broadcast()
            )
        try:
            result = txn.wait()
            if not result["receipt"].get("result"):
                raise TransactionError("Transaction failed")
        except Exception as exc:
            raise TransactionError(f"Tron transaction error: {exc}") from exc
        return txn.txid

    # ------------------------------------------------------------------
    # Deposit listener (simple poller)
    # ------------------------------------------------------------------
    def listen_deposits(
        self,
        system_address: str,
        callback: DepositCallback,
        start_block: int | None = None,
    ) -> None:
        """Простейший опрос блоков для входящих TRX депозитов.

        Для production следует использовать событие контракта или webhook
        через TronGrid. Здесь пример для тестов и отладки.
        """
        from time import sleep

        last_block = start_block or self.client.get_latest_block()["number"]
        while True:
            current_block = self.client.get_latest_block()["number"]
            for block_num in range(last_block + 1, current_block + 1):
                block = self.client.get_block(block_num, full=True)
                for tx in block["transactions"]:
                    if tx["raw_data"]["contract"][0]["type"] != "TransferContract":
                        continue
                    to_addr = tx["raw_data"]["contract"][0]["parameter"]["value"][
                        "to_address"
                    ]
                    to_addr_base58 = Tron.address.from_hex(to_addr).base58
                    if to_addr_base58 != system_address:
                        continue
                    amount = int(tx["raw_data"]["contract"][0]["parameter"]["value"]["amount"])
                    callback(tx_hash=tx["txID"], address=to_addr_base58, amount=amount, raw_tx=tx)
            last_block = current_block
            sleep(3)
