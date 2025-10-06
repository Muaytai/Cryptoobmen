from __future__ import annotations

import logging
from decimal import Decimal
from typing import List, Dict, Any, Tuple

from .base import BaseBlockchainService

try:
    from xrpl.clients import JsonRpcClient
    from xrpl.models.requests import AccountTx, AccountInfo
    from xrpl.wallet import Wallet
    from xrpl.transaction.reliable_submission import submit_and_wait
    from xrpl.transaction import autofill_and_sign
    from xrpl.models.transactions import Payment
    from xrpl.utils import xrp_to_drops, drops_to_xrp
    from xrpl.account import get_balance as xrpl_get_balance
    from xrpl.core.addresscodec import classic_address_to_xaddress, is_valid_classic_address
    XRPL_AVAILABLE = True
except ImportError:
    XRPL_AVAILABLE = False

logger = logging.getLogger(__name__)

XRPL_NETWORKS = {
    'mainnet': "https://s1.ripple.com:51234",
    'testnet': "https://s.altnet.rippletest.net:51234",
}

def get_xrpl_client(network: str):
    """Создает клиент для подключения к XRP Ledger."""
    if not XRPL_AVAILABLE:
        logger.error("xrpl-py library is not available")
        return None
    
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
        
        if not XRPL_AVAILABLE:
            logger.error("XRP service cannot be initialized: xrpl-py library is not available")
            self.client = None
            return
            
        self.client = get_xrpl_client(self.network)
        logger.info(f"XRP service initialized for {self.network}")

    def get_transactions(self, address: str, min_timestamp: int = 0) -> List[Dict[str, Any]]:
        """
        Получает входящие транзакции для указанного XRP-адреса.
        """
        if not XRPL_AVAILABLE or not self.client:
            logger.warning("XRP transactions unavailable: xrpl-py library not available")
            return []
            
        try:
            # Запрос транзакций для аккаунта
            account_tx_request = AccountTx(
                account=address,
                ledger_index_min=-1,
                ledger_index_max=-1,
                limit=200
            )
            
            response = self.client.request(account_tx_request)
            
            if not response.is_successful():
                logger.error(f"Failed to get transactions for {address}: {response}")
                return []
            
            transactions = []
            
            for tx_data in response.result.get('transactions', []):
                tx = tx_data.get('tx', {})
                meta = tx_data.get('meta', {})
                
                # Проверяем только входящие платежи
                if tx.get('TransactionType') != 'Payment':
                    continue
                    
                # Проверяем, что это входящий платеж
                if tx.get('Destination') != address:
                    continue
                
                # Получаем сумму
                amount = tx.get('Amount')
                if isinstance(amount, str):
                    # XRP в drops
                    amount_drops = amount
                elif isinstance(amount, dict):
                    # Токен (не XRP)
                    continue  # Пока обрабатываем только XRP
                else:
                    continue
                
                # Получаем memo если есть
                memo = None
                memos = tx.get('Memos', [])
                if memos:
                    memo_data = memos[0].get('Memo', {})
                    memo_hex = memo_data.get('MemoData', '')
                    if memo_hex:
                        try:
                            memo = bytes.fromhex(memo_hex).decode('utf-8')
                        except:
                            memo = memo_hex
                
                # Проверяем успешность транзакции
                if meta.get('TransactionResult') != 'tesSUCCESS':
                    continue
                
                transactions.append({
                    'transaction_id': tx.get('hash'),
                    'value': amount_drops,
                    'memo': memo,
                    'block_height': tx_data.get('ledger_index'),
                    'confirmed': True  # Все транзакции в ledger уже подтверждены
                })
            
            logger.info(f"Found {len(transactions)} XRP transactions for {address}")
            return transactions
            
        except Exception as e:
            logger.error(f"Error getting XRP transactions for {address}: {e}")
            return []

    def get_balance(self, address: str) -> Decimal:
        """
        Получает баланс для указанного XRP-адреса.
        """
        if not XRPL_AVAILABLE or not self.client:
            logger.warning("XRP balance check unavailable: xrpl-py library not available")
            return Decimal('0.0')
            
        try:
            balance = xrpl_get_balance(address, self.client)
            # Конвертируем из drops в XRP, убеждаемся что balance это строка
            balance_str = str(balance) if not isinstance(balance, str) else balance
            return Decimal(drops_to_xrp(balance_str))
        except Exception as e:
            logger.error(f"Error getting XRP balance for {address}: {e}")
            return Decimal('0.0')

    def send_transaction(self, private_key: str, to_address: str, amount: Decimal, memo: str = "") -> str:
        """
        Отправляет транзакцию XRP.
        """
        if not XRPL_AVAILABLE or not self.client:
            logger.error("XRP transactions unavailable: xrpl-py library not available")
            raise Exception("XRP library not available")
            
        try:
            # Создаем кошелек из приватного ключа
            wallet = Wallet.from_seed(private_key)
            
            # Конвертируем amount в drops
            amount_drops = xrp_to_drops(amount)
            
            # Создаем транзакцию
            payment = Payment(
                account=wallet.classic_address,
                destination=to_address,
                amount=str(amount_drops)
            )
            
            # Добавляем memo если есть
            if memo:
                memo_hex = memo.encode('utf-8').hex().upper()
                payment.memos = [{
                    "Memo": {
                        "MemoData": memo_hex
                    }
                }]
            
            # Автозаполнение и подпись
            signed_tx = autofill_and_sign(payment, self.client, wallet)
            
            # Отправка транзакции
            response = submit_and_wait(signed_tx, self.client)
            
            if response.is_successful():
                tx_hash = response.result.get('hash')
                logger.info(f"XRP transaction sent successfully: {tx_hash}")
                return tx_hash
            else:
                raise Exception(f"Transaction failed: {response}")
                
        except Exception as e:
            logger.error(f"Error sending XRP transaction: {e}")
            raise Exception(f"Failed to send XRP transaction: {e}")
    
    def create_new_address(self, **kwargs) -> Tuple[str, str]:
        """
        Создает новый адрес для пользователя.
        """
        if not XRPL_AVAILABLE:
            logger.error("XRP address generation unavailable: xrpl-py library not available")
            raise Exception("XRP library not available")
            
        try:
            # Создаем новый кошелек
            wallet = Wallet.create()
            
            address = wallet.classic_address
            private_key = wallet.seed
            
            logger.info(f"Created new XRP address: {address}")
            return address, private_key
            
        except Exception as e:
            logger.error(f"Error creating XRP address: {e}")
            raise Exception(f"Failed to create XRP address: {e}")
    
    def validate_address(self, address: str) -> bool:
        """Валидирует XRP адрес."""
        if not XRPL_AVAILABLE:
            logger.warning("XRP address validation unavailable: xrpl-py library not available")
            return False
            
        try:
            return is_valid_classic_address(address)
        except Exception as e:
            logger.error(f"Error validating XRP address {address}: {e}")
            return False
