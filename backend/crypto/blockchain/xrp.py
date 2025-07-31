from __future__ import annotations

import logging
from decimal import Decimal
from typing import List, Dict, Any

from .base import BaseBlockchainService
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountTx, AccountInfo
from xrpl.wallet import Wallet
from xrpl.transaction import autofill_and_sign, submit_and_wait
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
            tx_data = tx.get("tx_json") or tx.get("tx", {})
            if tx_data.get("Destination") == address and tx_data.get("TransactionType") == "Payment":
                # Сумма может быть в Amount или DeliverMax
                value = tx_data.get('Amount') or tx_data.get('DeliverMax') or 0
                incoming.append({
                    'transaction_id': tx.get('hash') or tx_data.get('hash'),
                    'from_address': tx_data.get('Account'),
                    'to_address': tx_data.get('Destination'),
                    'value': str(value),  # в drops
                    'memo': str(tx_data.get('DestinationTag', '')) if tx_data.get('DestinationTag') else None
                })
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

    def send_transaction(self, seed: str, to_address: str, amount: Decimal, memo: str = "") -> str:
        """
        Отправляет транзакцию XRP.
        :param seed: seed (family seed) отправителя
        :param to_address: классический адрес получателя
        :param amount: сумма в XRP
        :param memo: DestinationTag (если нужно)
        :return: хэш транзакции
        """
        try:
            from xrpl.transaction import autofill, sign, submit_and_wait
            wallet = Wallet.from_seed(seed)
            from_address = wallet.classic_address
            amount_drops = xrp_to_drops(amount)
            # Обрабатываем memo для destination_tag
            destination_tag = None
            if memo:
                try:
                    # Если memo содержит withdrawal_ID_TRANSFER_ID, извлекаем ID
                    if memo.startswith('withdrawal_'):
                        parts = memo.split('_')
                        if len(parts) >= 2:
                            destination_tag = int(parts[1])  # Берем ID вывода
                    else:
                        # Если это просто число
                        destination_tag = int(memo)
                except (ValueError, IndexError):
                    # Если не удается преобразовать, используем None
                    destination_tag = None

            payment = Payment(
                account=from_address,
                amount=str(amount_drops),
                destination=to_address,
                destination_tag=destination_tag
            )

            # 1. Autofill (fee, sequence, и т.д.)
            tx = autofill(payment, self.client)

            # 2. Подпись
            signed_tx = sign(tx, wallet)

            # 3. Отправка и ожидание
            response = submit_and_wait(signed_tx, self.client)
            tx_hash = response.result.get("hash")
            return tx_hash
        except Exception as e:
            logger.error(f"[XRPService.send_transaction] Ошибка отправки XRP: {e}")
            raise
    
    def create_new_address(self, user_id: int = None) -> tuple[str, str]:
        """
        Создает новый адрес для пользователя.
        Возвращает кортеж (адрес, приватный ключ).
        """
        wallet = Wallet.create()
        return wallet.classic_address, wallet.seed
