from bitcoinlib.wallets import Wallet, wallet_delete
from bitcoinlib.services.services import Service
from decimal import Decimal
from typing import List, Dict, Any, Tuple
import os
from blockcypher import get_address_details
from datetime import datetime

from .base import BaseBlockchainService

class BitcoinService(BaseBlockchainService):
    def __init__(self, network='testnet'):
        super().__init__(network)
        # bitcoinlib использует 'bitcoin' для mainnet и 'testnet' для testnet
        self.service = Service(network=self.network if self.network == 'testnet' else 'bitcoin')
        self.coin_symbol = 'btc-testnet' if network == 'testnet' else 'btc'

    def get_transactions(self, address: str, min_timestamp: int = 0) -> List[Dict[str, Any]]:
        """Получает транзакции для адреса."""
        try:
            details = get_address_details(address, coin_symbol=self.coin_symbol)
            txs = []
            if 'txrefs' in details:
                for tx_ref in details['txrefs']:
                    # Blockcypher не предоставляет timestamp для txrefs, поэтому мы не можем фильтровать по min_timestamp
                    # Мы просто вернем все транзакции
                    if tx_ref['tx_output_n'] >= 0: # Это входящая транзакция
                        txs.append({
                            'transaction_id': tx_ref['tx_hash'],
                            'value': str(tx_ref['value']),
                            'memo': None
                        })
            return txs
        except Exception as e:
            print(f"Error getting transactions for {address}: {e}")
            return []

    def send_transaction(self, private_key: str, to_address: str, amount: Decimal, memo: str = "") -> str:
        """Отправляет транзакцию."""
        # Требует более сложной логики с управлением UTXO.
        # Оставим заглушку.
        pass

    def get_balance(self, address: str) -> Decimal:
        """Получает баланс адреса."""
        try:
            # У bitcoinlib нет прямого метода для получения баланса по адресу без кошелька.
            # Это потребует использования провайдера, такого как Blockstream.
            # Для простоты оставим заглушку.
            return Decimal('0.0')
        except Exception:
            return Decimal('0.0')

    def create_new_address(self, **kwargs) -> Tuple[str, str]:
        """
        Создает новый адрес и возвращает его вместе с приватным ключом.
        """
        wallet_name = f"temp_wallet_{os.urandom(8).hex()}"
        try:
            wallet = Wallet.create(wallet_name, network=self.network)
            key = wallet.get_key()
            address = key.address
            private_key_wif = key.wif
            return address, private_key_wif
        finally:
            # Гарантированно удаляем временный кошелек
            if os.path.exists(f"{wallet_name}.db"):
                 wallet_delete(wallet_name, force=True)


    def validate_address(self, address: str) -> bool:
        """Валидирует адрес."""
        # TODO: Реализовать валидацию
        return True
