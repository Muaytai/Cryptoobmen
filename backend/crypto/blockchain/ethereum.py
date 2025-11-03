"""Service for interacting with the Ethereum blockchain (ETH and ERC-20 tokens)."""
from __future__ import annotations

import logging
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional
from decimal import Decimal

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from eth_account import Account
from eth_utils import to_checksum_address, is_address
from hexbytes import HexBytes
from django.conf import settings

from .base import BaseBlockchainService

logger = logging.getLogger(__name__)

# Standard ERC-20 ABI (минимальный набор для работы с токенами)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    }
]


class EthereumError(RuntimeError):
    """Raised when Ethereum operations fail."""


class EthereumService(BaseBlockchainService):
    """
    Service for interacting with the Ethereum blockchain.
    Supports both ETH and ERC-20 token operations.
    """

    def __init__(self, network: str = 'goerli'):
        super().__init__(network)
        self.w3 = self._initialize_web3()
        self.gas_price_multiplier = settings.ETHEREUM_GAS_PRICE_MULTIPLIER
        self.max_gas_price = Web3.to_wei(settings.ETHEREUM_MAX_GAS_PRICE, 'gwei')
        self.gas_limit_eth = settings.ETHEREUM_GAS_LIMIT_ETH
        self.gas_limit_erc20 = settings.ETHEREUM_GAS_LIMIT_ERC20

    def _initialize_web3(self) -> Web3:
        """Initialize Web3 connection with fallback RPC."""
        rpc_url = settings.ETHEREUM_RPC_URL
        backup_rpc_url = settings.ETHEREUM_BACKUP_RPC_URL

        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            # Add PoA middleware for testnets like Goerli
            if self.network in ['goerli', 'sepolia']:
                w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
            
            if w3.is_connected():
                logger.info(f"Connected to Ethereum {self.network} via primary RPC")
                return w3
            else:
                raise ConnectionError("Primary RPC connection failed")
                
        except Exception as e:
            logger.warning(f"Primary RPC failed: {e}")
            
            if backup_rpc_url:
                try:
                    w3 = Web3(Web3.HTTPProvider(backup_rpc_url))
                    if self.network in ['goerli', 'sepolia']:
                        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                    
                    if w3.is_connected():
                        logger.info(f"Connected to Ethereum {self.network} via backup RPC")
                        return w3
                except Exception as backup_e:
                    logger.error(f"Backup RPC also failed: {backup_e}")
            
            raise EthereumError(f"Failed to connect to Ethereum network: {e}")

    def _get_contract(self, contract_address: str):
        """Get ERC-20 contract instance."""
        if not is_address(contract_address):
            raise ValueError(f"Invalid contract address: {contract_address}")
        
        checksum_address = to_checksum_address(contract_address)
        return self.w3.eth.contract(address=checksum_address, abi=ERC20_ABI)

    def _estimate_gas_price(self) -> int:
        """Estimate optimal gas price with multiplier."""
        try:
            base_gas_price = self.w3.eth.gas_price
            adjusted_price = int(base_gas_price * self.gas_price_multiplier)
            
            # Cap at maximum gas price
            return min(adjusted_price, self.max_gas_price)
        except Exception as e:
            logger.warning(f"Failed to estimate gas price: {e}")
            return Web3.to_wei(20, 'gwei')  # Fallback to 20 Gwei

    def get_transactions(self, address: str, min_timestamp: int = 0, contract_address: str = None) -> List[Dict[str, Any]]:
        """
        Get incoming transactions for an address.
        
        :param address: Ethereum address to check
        :param min_timestamp: Minimum timestamp in milliseconds
        :param contract_address: ERC-20 contract address (None for ETH)
        :return: List of transaction dictionaries
        """
        if not is_address(address):
            logger.warning(f"Invalid Ethereum address: {address}")
            return []

        checksum_address = to_checksum_address(address)
        transactions = []

        try:
            # Get latest block number
            latest_block = self.w3.eth.block_number
            
            # Calculate starting block from timestamp (approximate)
            # Ethereum block time is ~12-15 seconds
            blocks_to_scan = min(1000, latest_block)  # Limit scan range
            start_block = max(0, latest_block - blocks_to_scan)

            if contract_address:
                # Scan for ERC-20 token transfers
                transactions = self._scan_erc20_transfers(
                    checksum_address, contract_address, start_block, latest_block, min_timestamp
                )
            else:
                # Scan for ETH transfers
                transactions = self._scan_eth_transfers(
                    checksum_address, start_block, latest_block, min_timestamp
                )

        except Exception as e:
            logger.error(f"Error scanning transactions for {address}: {e}")

        return transactions

    def _scan_eth_transfers(self, address: str, start_block: int, end_block: int, min_timestamp: int) -> List[Dict[str, Any]]:
        """Scan for incoming ETH transfers."""
        transactions = []
        
        try:
            for block_num in range(start_block, end_block + 1):
                block = self.w3.eth.get_block(block_num, full_transactions=True)
                block_timestamp = block.timestamp * 1000  # Convert to milliseconds
                
                if block_timestamp < min_timestamp:
                    continue

                for tx in block.transactions:
                    if tx.to and tx.to.lower() == address.lower() and tx.value > 0:
                        transactions.append({
                            'transaction_id': tx.hash.hex(),
                            'from_address': tx['from'],
                            'to_address': tx.to,
                            'value': str(tx.value),  # Wei amount
                            'block_number': block_num,
                            'timestamp': block_timestamp,
                            'memo': None
                        })
        except Exception as e:
            logger.error(f"Error scanning ETH transfers: {e}")

        return transactions

    def _scan_erc20_transfers(self, address: str, contract_address: str, start_block: int, end_block: int, min_timestamp: int) -> List[Dict[str, Any]]:
        """Scan for incoming ERC-20 token transfers."""
        transactions = []
        
        try:
            contract = self._get_contract(contract_address)
            
            # Get Transfer events where 'to' is our address
            transfer_filter = contract.events.Transfer.create_filter(
                fromBlock=start_block,
                toBlock=end_block,
                argument_filters={'to': address}
            )
            
            events = transfer_filter.get_all_entries()
            
            for event in events:
                block = self.w3.eth.get_block(event.blockNumber)
                block_timestamp = block.timestamp * 1000
                
                if block_timestamp < min_timestamp:
                    continue

                transactions.append({
                    'transaction_id': event.transactionHash.hex(),
                    'from_address': event.args['from'],
                    'to_address': event.args.to,
                    'value': str(event.args.value),  # Token amount in smallest unit
                    'block_number': event.blockNumber,
                    'timestamp': block_timestamp,
                    'memo': None,
                    'contract_address': contract_address
                })
                
        except Exception as e:
            logger.error(f"Error scanning ERC-20 transfers: {e}")

        return transactions

    def send_transaction(self, private_key: str, to_address: str, amount: Decimal, memo: str = "", contract_address: str = None) -> str:
        """
        Send ETH or ERC-20 tokens.
        
        :param private_key: Sender's private key
        :param to_address: Recipient address
        :param amount: Amount to send (in main units, e.g., ETH or tokens)
        :param memo: Transaction memo (not used in Ethereum)
        :param contract_address: ERC-20 contract address (None for ETH)
        :return: Transaction hash
        """
        if not is_address(to_address):
            raise ValueError(f"Invalid recipient address: {to_address}")

        try:
            account = Account.from_key(private_key)
            from_address = account.address
            to_address = to_checksum_address(to_address)

            if contract_address:
                return self._send_erc20_transaction(account, to_address, amount, contract_address)
            else:
                return self._send_eth_transaction(account, to_address, amount)

        except Exception as e:
            logger.error(f"Error sending transaction: {e}")
            raise EthereumError(f"Failed to send transaction: {e}")

    def _send_eth_transaction(self, account: Account, to_address: str, amount: Decimal) -> str:
        """Send ETH transaction."""
        nonce = self.w3.eth.get_transaction_count(account.address)
        gas_price = self._estimate_gas_price()
        
        # Convert ETH to Wei
        value_wei = Web3.to_wei(amount, 'ether')
        
        transaction = {
            'to': to_address,
            'value': value_wei,
            'gas': self.gas_limit_eth,
            'gasPrice': gas_price,
            'nonce': nonce,
        }
        
        signed_txn = self.w3.eth.account.sign_transaction(transaction, account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        logger.info(f"Sent {amount} ETH from {account.address} to {to_address}, tx: {tx_hash.hex()}")
        return tx_hash.hex()

    def _send_erc20_transaction(self, account: Account, to_address: str, amount: Decimal, contract_address: str) -> str:
        """Send ERC-20 token transaction."""
        contract = self._get_contract(contract_address)
        
        # Get token decimals
        decimals = contract.functions.decimals().call()
        
        # Convert amount to token's smallest unit
        token_amount = self.to_atomic_unit(amount, decimals)
        
        nonce = self.w3.eth.get_transaction_count(account.address)
        gas_price = self._estimate_gas_price()
        
        # Build transaction
        transaction = contract.functions.transfer(to_address, token_amount).build_transaction({
            'from': account.address,
            'gas': self.gas_limit_erc20,
            'gasPrice': gas_price,
            'nonce': nonce,
        })
        
        signed_txn = self.w3.eth.account.sign_transaction(transaction, account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        logger.info(f"Sent {amount} tokens from {account.address} to {to_address}, tx: {tx_hash.hex()}")
        return tx_hash.hex()

    def get_balance(self, address: str, contract_address: str = None) -> Decimal:
        """
        Get balance for an address.
        
        :param address: Address to check
        :param contract_address: ERC-20 contract address (None for ETH)
        :return: Balance in main units
        """
        if not is_address(address):
            logger.warning(f"Invalid address: {address}")
            return Decimal('0.0')

        checksum_address = to_checksum_address(address)

        try:
            if contract_address:
                # Get ERC-20 token balance
                contract = self._get_contract(contract_address)
                balance_raw = contract.functions.balanceOf(checksum_address).call()
                decimals = contract.functions.decimals().call()
                return self.from_atomic_unit(balance_raw, decimals)
            else:
                # Get ETH balance
                balance_wei = self.w3.eth.get_balance(checksum_address)
                return Web3.from_wei(balance_wei, 'ether')

        except Exception as e:
            logger.error(f"Error getting balance for {address}: {e}")
            return Decimal('0.0')

    def create_new_address(self, **kwargs) -> Tuple[str, str]:
        """
        Create a new Ethereum address.
        
        :return: Tuple of (address, private_key)
        """
        try:
            account = Account.create()
            address = account.address
            private_key = account.key.hex()
            
            logger.info(f"Generated new Ethereum address: {address}")
            return address, private_key
            
        except Exception as e:
            logger.error(f"Error creating new Ethereum address: {e}")
            raise EthereumError(f"Failed to create new address: {e}")

    def validate_address(self, address: str) -> bool:
        """Validate Ethereum address."""
        return is_address(address)

    def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Get transaction receipt by hash."""
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            return {
                'transaction_hash': receipt.transactionHash.hex(),
                'block_number': receipt.blockNumber,
                'gas_used': receipt.gasUsed,
                'status': receipt.status,  # 1 for success, 0 for failure
            }
        except Exception as e:
            logger.error(f"Error getting transaction receipt for {tx_hash}: {e}")
            return None

    def is_transaction_confirmed(self, tx_hash: str, required_confirmations: int = 12) -> bool:
        """
        Check if transaction is confirmed with required number of confirmations.
        
        :param tx_hash: Transaction hash
        :param required_confirmations: Number of required confirmations (default: 12 for security)
        :return: True if confirmed
        """
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            if receipt is None:
                return False
            
            # Проверяем статус транзакции (1 = success, 0 = failed)
            if receipt.status == 0:
                logger.warning(f"Transaction {tx_hash} failed (status=0)")
                return False
            
            current_block = self.w3.eth.block_number
            confirmations = current_block - receipt.blockNumber
            
            is_confirmed = confirmations >= required_confirmations
            logger.debug(f"Transaction {tx_hash}: {confirmations} confirmations (required: {required_confirmations})")
            
            return is_confirmed
            
        except Exception as e:
            logger.warning(f"Failed to check transaction confirmation for {tx_hash}: {e}")
            return False

    def estimate_gas_cost(self, from_address: str, to_address: str, amount_wei: int) -> Decimal:
        """
        Оценивает стоимость газа для ETH транзакции с учетом реальной оценки через RPC.
        
        :param from_address: Адрес отправителя
        :param to_address: Адрес получателя
        :param amount_wei: Сумма в Wei
        :return: Стоимость газа в ETH
        """
        try:
            # Получаем текущую цену газа
            gas_price = self._estimate_gas_price()
            
            # Оцениваем количество газа для транзакции через RPC
            gas_estimate = self.w3.eth.estimate_gas({
                'from': to_checksum_address(from_address),
                'to': to_checksum_address(to_address),
                'value': amount_wei
            })
            
            # Рассчитываем общую стоимость газа в wei
            gas_cost_wei = gas_price * gas_estimate
            
            # Применяем коэффициент безопасности 1.1
            # gas_cost_wei - это int, поэтому умножаем как int и приводим к int
            gas_cost_wei_with_buffer = int(Decimal(gas_cost_wei) * Decimal('1.1'))
            
            # Конвертируем в ETH
            gas_cost_eth = Web3.from_wei(gas_cost_wei_with_buffer, 'ether')
            
            logger.info(f"Gas estimation: price={gas_price}, estimate={gas_estimate}, cost={gas_cost_eth} ETH (with 1.1x buffer)")
            
            return Decimal(str(gas_cost_eth))
            
        except Exception as e:
            logger.error(f"Failed to estimate gas cost: {e}")
            # Fallback к фиксированному значению
            return Decimal('0.005')
    
    def get_max_sendable_amount(self, address: str, to_address: str) -> Decimal:
        """
        Рассчитывает максимальную сумму ETH, которую можно отправить с адреса (баланс - газ).
        
        ⚠️ ВАЖНО: Для ETH газ вычитается из того же баланса ETH, поэтому нужно точно рассчитать,
        чтобы на адресе осталось достаточно для оплаты газа.
        
        :param address: Адрес отправителя
        :param to_address: Адрес получателя
        :return: Максимальная сумма для отправки в ETH
        """
        try:
            balance = self.get_balance(address)
            if balance <= 0:
                return Decimal('0')
            
            # Конвертируем баланс в wei для оценки газа
            balance_wei = Web3.to_wei(balance, 'ether')
            
            # Оцениваем стоимость газа для отправки всего баланса
            # Важно: gas будет вычитаться из того же баланса, поэтому нужно итеративно найти оптимальную сумму
            gas_cost = self.estimate_gas_cost(address, to_address, balance_wei)
            
            # Максимальная отправляемая сумма = баланс - газ
            max_sendable = balance - gas_cost
            
            # Если после вычитания газа сумма слишком мала или отрицательная
            if max_sendable <= 0:
                logger.warning(f"Cannot send from {address}: balance {balance} ETH, gas cost {gas_cost} ETH")
                return Decimal('0')
            
            # Дополнительная проверка: уточняем оценку газа для полученной суммы
            # (газ может немного отличаться для меньшей суммы)
            max_sendable_wei = Web3.to_wei(max_sendable, 'ether')
            refined_gas_cost = self.estimate_gas_cost(address, to_address, max_sendable_wei)
            refined_max_sendable = balance - refined_gas_cost
            
            if refined_max_sendable <= 0:
                logger.warning(f"Refined calculation: balance {balance} ETH, refined gas {refined_gas_cost} ETH")
                return Decimal('0')
            
            logger.info(f"Max sendable from {address}: {refined_max_sendable} ETH (balance: {balance}, gas: {refined_gas_cost})")
            return refined_max_sendable
            
        except Exception as e:
            logger.error(f"Failed to calculate max sendable amount: {e}")
            return Decimal('0')
    
    def estimate_gas_fee(self, to_address: str, amount: Decimal, contract_address: str = None) -> Dict[str, Decimal]:
        """
        Estimate gas fee for a transaction.
        
        :return: Dictionary with gas estimates in ETH
        """
        try:
            gas_price = self._estimate_gas_price()
            
            if contract_address:
                gas_limit = self.gas_limit_erc20
            else:
                gas_limit = self.gas_limit_eth
            
            gas_fee_wei = gas_price * gas_limit
            gas_fee_eth = Web3.from_wei(gas_fee_wei, 'ether')
            
            return {
                'gas_price_gwei': Web3.from_wei(gas_price, 'gwei'),
                'gas_limit': gas_limit,
                'gas_fee_eth': gas_fee_eth,
                'gas_fee_usd': Decimal('0.0')  # TODO: Calculate USD equivalent
            }
            
        except Exception as e:
            logger.error(f"Error estimating gas fee: {e}")
            return {
                'gas_price_gwei': Decimal('20'),
                'gas_limit': 21000,
                'gas_fee_eth': Decimal('0.0042'),
                'gas_fee_usd': Decimal('0.0')
            }