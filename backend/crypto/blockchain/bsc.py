"""Service for interacting with Binance Smart Chain (BNB native, BEP-20 compatible)."""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Dict, Any, List, Tuple, Optional

from django.conf import settings
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from eth_account import Account
from eth_utils import to_checksum_address, is_address

from .ethereum import EthereumService, EthereumError

logger = logging.getLogger(__name__)


class BSCError(EthereumError):
    """Raised when BSC operations fail."""


class BSCService(EthereumService):
    """
    Service for Binance Smart Chain native BNB transfers and BEP-20 tokens (ERC-20 compatible).
    Inherits EthereumService behavior, overrides RPC and gas defaults for BSC.
    """

    def __init__(self, network: str = 'mainnet'):
        # network: 'mainnet' or 'testnet'
        self.network = network
        # Configure RPCs from settings or use sane defaults
        self._primary_rpc_url, self._backup_rpc_url = self._resolve_rpc_urls(network)
        # Gas settings (BSC typical params)
        self._gas_price_multiplier = getattr(settings, 'ETHEREUM_GAS_PRICE_MULTIPLIER', 1.1)
        self._max_gas_price_gwei = int(getattr(settings, 'ETHEREUM_MAX_GAS_PRICE', 50))
        self._gas_limit_native = int(getattr(settings, 'ETHEREUM_GAS_LIMIT_ETH', 21000))
        self._gas_limit_erc20 = int(getattr(settings, 'ETHEREUM_GAS_LIMIT_ERC20', 65000))

        # Initialize Web3
        self.w3 = self._initialize_web3()

    # --- Overrides of base configuration accessors used by EthereumService ---
    def _initialize_web3(self) -> Web3:
        """Initialize Web3 connection for BSC with fallback RPC.

        Важно: генерация нового адреса не требует активного соединения с RPC.
        Поэтому при недоступности RPC не выбрасываем исключение, а возвращаем
        экземпляр Web3 с провайдером — это позволит продолжить операции,
        не требующие сети (например, создание пар ключей).
        """
        # Пытаемся подключиться к основному RPC
        try:
            w3 = Web3(Web3.HTTPProvider(self._primary_rpc_url))
            w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
            if w3.is_connected():
                logger.info(f"Connected to BSC {self.network} via primary RPC")
                return w3
            else:
                raise ConnectionError("Primary RPC connection failed")
        except Exception as e:
            logger.warning(f"Primary BSC RPC failed: {e}")
            # Пробуем резервный RPC
            if self._backup_rpc_url:
                try:
                    w3 = Web3(Web3.HTTPProvider(self._backup_rpc_url))
                    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                    if w3.is_connected():
                        logger.info(f"Connected to BSC {self.network} via backup RPC")
                        return w3
                except Exception as backup_e:
                    logger.error(f"Backup BSC RPC also failed: {backup_e}")
            # "Мягкий" режим: возвращаем Web3 даже без активного соединения
            logger.warning("BSC RPC not reachable; proceeding in offline-capable mode for address generation")
            return Web3(Web3.HTTPProvider(self._primary_rpc_url))

    def _estimate_gas_price(self) -> int:
        try:
            base_gas_price = self.w3.eth.gas_price
            adjusted = int(base_gas_price * self._gas_price_multiplier)
            return min(adjusted, Web3.to_wei(self._max_gas_price_gwei, 'gwei'))
        except Exception as e:
            logger.warning(f"Failed to estimate BSC gas price: {e}")
            return Web3.to_wei(3, 'gwei')  # conservative fallback

    def _send_eth_transaction(self, account: Account, to_address: str, amount: Decimal) -> str:  # type: ignore[override]
        """Send BNB transaction (native)."""
        nonce = self.w3.eth.get_transaction_count(account.address)
        gas_price = self._estimate_gas_price()
        value_wei = Web3.to_wei(amount, 'ether')
        chain_id = self.w3.eth.chain_id
        tx = {
            'to': to_address,
            'value': value_wei,
            'gas': self._gas_limit_native,
            'gasPrice': gas_price,
            'nonce': nonce,
            'chainId': chain_id,
        }
        signed = self.w3.eth.account.sign_transaction(tx, account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        logger.info(f"Sent {amount} BNB from {account.address} to {to_address}, tx: {tx_hash.hex()}")
        return tx_hash.hex()

    def _send_erc20_transaction(self, account: Account, to_address: str, amount: Decimal, contract_address: str) -> str:  # type: ignore[override]
        # Reuse parent behavior, but gas limit from BSC settings
        contract = self._get_contract(contract_address)
        decimals = contract.functions.decimals().call()
        token_amount = self.to_atomic_unit(amount, decimals)
        nonce = self.w3.eth.get_transaction_count(account.address)
        gas_price = self._estimate_gas_price()
        chain_id = self.w3.eth.chain_id
        tx = contract.functions.transfer(to_address, token_amount).build_transaction({
            'from': account.address,
            'gas': self._gas_limit_erc20,
            'gasPrice': gas_price,
            'nonce': nonce,
            'chainId': chain_id,
        })
        signed = self.w3.eth.account.sign_transaction(tx, account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        logger.info(f"Sent {amount} BEP-20 from {account.address} to {to_address}, tx: {tx_hash.hex()}")
        return tx_hash.hex()

    def create_new_address(self, **kwargs) -> Tuple[str, str]:
        try:
            account = Account.create()
            return account.address, account.key.hex()
        except Exception as e:
            logger.error(f"Error creating new BSC address: {e}")
            raise BSCError(f"Failed to create new BSC address: {e}")

    def validate_address(self, address: str) -> bool:
        return is_address(address)

    # --- Helpers ---
    @staticmethod
    def _resolve_rpc_urls(network: str) -> Tuple[str, Optional[str]]:
        if network == 'testnet':
            primary = getattr(settings, 'BSC_TESTNET_RPC_URL', 'https://data-seed-prebsc-1-s1.binance.org:8545/')
            backup = getattr(settings, 'BSC_TESTNET_BACKUP_RPC_URL', '') or None
        else:
            primary = getattr(settings, 'BSC_RPC_URL', 'https://bsc-dataseed.binance.org')
            backup = getattr(settings, 'BSC_BACKUP_RPC_URL', '') or None
        return primary, backup






