from __future__ import annotations

import logging
from decimal import Decimal
from typing import List, Dict, Any

from .base import BaseBlockchainService
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountTx, AccountInfo
from xrpl.wallet import Wallet
from xrpl.transaction.reliable_submission import submit_and_wait
from xrpl.transaction import autofill_and_sign
from xrpl.models.transactions import Payment
from xrpl.utils import xrp_to_drops
from xrpl.account import get_balance as xrpl_get_balance
from xrpl.core.addresscodec import classic_address_to_xaddress

logger = logging.getLogger(__name__)

XRPL_NETWORKS = {
    'mainnet': "https://s1.ripple.com:51234",
    'testnet': "https://s.altnet.rippletest.net:51234",
}

def get_xrpl_client(network: str) -> JsonRpcClient:
    url = XRPL_NETWORKS.get(network, XRPL_NETWORKS['testnet'])
    return JsonRpcClient(url)

class XRPService(BaseBlockchainService):
    """
    Сервис для взаимодействия с XRP Ledger (Ripple).
    Реализует интерфейс BaseBlockchainService.
    """
    def __init__(self, network: str = 'testnet'):
        super().__init__(network)
        if self.network not in XRPL_NETWORKS:
            raise ValueError("Network must be 'mainnet' or 'testnet'")
        self.client = get_xrpl_client(self.network)

    def get_transactions(self, address: str, min_timestamp: int = 0) -> List[Dict[str, Any]]:
        """
        Получает входящие транзакции для указанного XRP-адреса.
        min_timestamp не используется, так как xrpl возвращает ledger index, а не timestamp.
        """
        req = AccountTx(account=address)
        response = self.client.request(req)
        txs = response.result.get("transactions", [])
        incoming = []
        for tx in txs:
            tx_data = tx.get("tx", {})
            if tx_data.get("Destination") == address and tx_data.get("TransactionType") == "Payment":
                incoming.append({
                    'transaction_id': tx_data.get('hash'),
                    'from_address': tx_data.get('Account'),
                    'to_address': tx_data.get('Destination'),
                    'value': str(tx_data.get('Amount', 0)),  # в drops
                    'memo': str(tx_data.get('DestinationTag', '')) if tx_data.get('DestinationTag') else None
                })
        logger.info(f"[XRPService.get_transactions] Found {len(incoming)} incoming payments for {address}")
        return incoming

    def get_balance(self, address: str) -> Decimal:
        """
        Получает баланс для указанного XRP-адреса.
        """
        try:
            # xrpl.account.get_balance возвращает баланс в drops (int)
            balance_drops = xrpl_get_balance(address, self.client)
            return self.from_atomic_unit(balance_drops, 6)  # 1 XRP = 1_000_000 drops
        except Exception as e:
            logger.error(f"[XRPService.get_balance] Ошибка получения баланса для {address}: {e}")
            return Decimal('0.0')

    def send_transaction(self, private_key: str, to_address: str, amount: Decimal, memo: str = "") -> str:
        """
        Отправляет транзакцию XRP.
        :param private_key: seed (family seed) отправителя
        :param to_address: классический адрес получателя
        :param amount: сумма в XRP
        :param memo: DestinationTag (если нужно)
        :return: хэш транзакции
        """
        try:
            # Для xrpl-py seed используется для создания Wallet
            wallet = Wallet(seed=private_key, sequence=0)
            from_address = wallet.classic_address
            amount_drops = xrp_to_drops(amount)
            destination_tag = int(memo.replace('withdrawal_', '').split('_')[0]) if memo and memo.startswith('withdrawal_') else None
            payment = Payment(
                account=from_address,
                amount=str(amount_drops),
                destination=to_address,
                destination_tag=destination_tag
            )
            tx = autofill_and_sign(payment, wallet, self.client)
            response = submit_and_wait(tx, self.client)
            tx_hash = response.result.get("hash")
            logger.info(f"[XRPService.send_transaction] Sent {amount} XRP from {from_address} to {to_address}, tx_hash={tx_hash}")
            return tx_hash
        except Exception as e:
            logger.error(f"[XRPService.send_transaction] Ошибка отправки XRP: {e}")
            raise 