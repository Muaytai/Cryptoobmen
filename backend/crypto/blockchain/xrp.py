import logging
from typing import List, Dict, Any
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountTx

logger = logging.getLogger(__name__)

XRPL_TESTNET_URL = "https://s.altnet.rippletest.net:51234"

def get_xrp_incoming_transactions(address: str, min_ledger: int = None) -> List[Dict[str, Any]]:
    """
    Получить входящие транзакции на адрес XRP Ledger testnet.
    :param address: XRP адрес
    :param min_ledger: минимальный номер ledger для фильтрации (опционально)
    :return: список транзакций
    """
    client = JsonRpcClient(XRPL_TESTNET_URL)
    req = AccountTx(account=address)
    if min_ledger:
        req.min_ledger = min_ledger
    response = client.request(req)
    txs = response.result.get("transactions", [])
    incoming = []
    for tx in txs:
        tx_data = tx.get("tx", {})
        if tx_data.get("Destination") == address and tx_data.get("TransactionType") == "Payment":
            incoming.append(tx_data)
    logger.info(f"[get_xrp_incoming_transactions] Found {len(incoming)} incoming payments for {address}")
    return incoming 