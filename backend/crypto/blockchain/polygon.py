"""Service for interacting with the Polygon blockchain (POL native currency only)."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from decimal import Decimal
from django.utils import timezone as django_timezone

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from eth_account import Account
from eth_utils import to_checksum_address, is_address
from django.conf import settings

from .base import BaseBlockchainService

logger = logging.getLogger(__name__)


class PolygonError(RuntimeError):
    """Raised when Polygon operations fail."""


class PolygonService(BaseBlockchainService):
    """
    Service for interacting with the Polygon blockchain.
    Supports POL (native Polygon token) operations only.
    """

    def __init__(self, network: str = None):
        # Используем настройку из settings.py если network не указан
        if network is None:
            network = getattr(settings, 'POLYGON_NETWORK', 'mainnet')
        super().__init__(network)
        self.w3 = self._initialize_web3()
        self.gas_price_multiplier = settings.POLYGON_GAS_PRICE_MULTIPLIER
        self.max_gas_price = Web3.to_wei(settings.POLYGON_MAX_GAS_PRICE, 'gwei')
        self.gas_limit = settings.POLYGON_GAS_LIMIT

    def _initialize_web3(self) -> Web3:
        """Initialize Web3 connection to Polygon network."""
        rpc_url = settings.POLYGON_RPC_URL
        backup_rpc_url = settings.POLYGON_BACKUP_RPC_URL

        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            # КРИТИЧЕСКИ ВАЖНО: Добавляем PoA middleware для Polygon
            # Polygon использует Proof of Authority консенсус
            w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
            logger.info("PoA middleware (ExtraDataToPOAMiddleware) успешно добавлен для Polygon")
                
            # Настройка логирования для подавления PoA предупреждений
            import logging
            web3_logger = logging.getLogger('web3.manager')
            web3_logger.setLevel(logging.ERROR)  # Подавляем WARNING уровень
            
            if not w3.is_connected():
                if backup_rpc_url:
                    logger.warning(f"Primary Polygon RPC failed, trying backup: {backup_rpc_url}")
                    w3 = Web3(Web3.HTTPProvider(backup_rpc_url))
                    # КРИТИЧЕСКИ ВАЖНО: Добавляем middleware и для backup RPC
                    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                    logger.info("PoA middleware добавлен для backup RPC")
                    # Настройка логирования и для backup RPC
                    web3_logger = logging.getLogger('web3.manager')
                    web3_logger.setLevel(logging.ERROR)
                
                if not w3.is_connected():
                    raise PolygonError("Failed to connect to Polygon network")
            
            # Проверяем что это действительно Polygon сеть
            try:
                chain_id = w3.eth.chain_id
                if self.network == 'mainnet':
                    expected_chain_id = 137
                elif self.network in ['testnet', 'amoy']:
                    expected_chain_id = 80002  # Amoy testnet (новый testnet)
                elif self.network == 'mumbai':
                    expected_chain_id = 80001  # Mumbai testnet (устаревший)
                else:
                    expected_chain_id = None
                    
                if expected_chain_id and chain_id != expected_chain_id:
                    logger.warning(f"Chain ID mismatch. Expected: {expected_chain_id}, Got: {chain_id}")
                else:
                    logger.info(f"Connected to correct Polygon network. Chain ID: {chain_id}")
            except Exception as e:
                logger.warning(f"Could not verify chain ID: {e}")
            
            logger.info(f"Connected to Polygon {self.network} network")
            return w3
            
        except Exception as e:
            logger.error(f"Failed to initialize Polygon Web3: {e}")
            raise PolygonError(f"Web3 initialization failed: {e}")

    def create_new_address(self, **kwargs) -> Tuple[str, str]:
        """
        Create a new Polygon address for deposits.
        
        :return: Tuple of (address, private_key)
        """
        try:
            # Генерируем новый аккаунт
            account = Account.create()
            address = account.address
            private_key = account.key.hex()
            
            logger.info(f"Generated new Polygon address: {address}")
            return address, private_key
            
        except Exception as e:
            logger.error(f"Failed to create new Polygon address: {e}")
            raise PolygonError(f"Address generation failed: {e}")

    def get_balance(self, address: str) -> Decimal:
        """
        Get POL balance for the specified address.
        
        :param address: Wallet address
        :return: Balance in POL as Decimal
        """
        try:
            if not address or not is_address(address):
                raise PolygonError(f"Invalid address format: {address}")
                
            checksum_address = to_checksum_address(address)
            balance_wei = self.w3.eth.get_balance(checksum_address)
            balance_pol = Web3.from_wei(balance_wei, 'ether')
            
            logger.debug(f"Polygon POL balance for {address}: {balance_pol}")
            return Decimal(str(balance_pol))
            
        except Exception as e:
            logger.error(f"Failed to get Polygon balance for {address}: {e}")
            return Decimal('0')

    def get_transactions(self, address: str, min_timestamp: int = 0, from_block: int = None, to_block: int = None) -> List[Dict[str, Any]]:
        """
        Get incoming POL transactions for the specified address.
        Uses optimized block scanning with early termination and caching.
        
        :param address: Wallet address to check
        :param min_timestamp: Minimum timestamp for transactions (in milliseconds)
        :return: List of transaction dictionaries
        """
        try:
            if not address or not is_address(address):
                raise PolygonError(f"Invalid address format: {address}")
                
            checksum_address = to_checksum_address(address)
            transactions = []
            
            # Определяем диапазон блоков для сканирования
            latest_block = self.w3.eth.block_number
            
            # Если переданы конкретные блоки, используем их
            if from_block is not None and to_block is not None:
                min_block = from_block
                scan_to_block = min(to_block, latest_block)
                logger.info(f"Custom block range: {min_block} to {scan_to_block}")
            elif min_timestamp > 0:
                # Если есть min_timestamp, сканируем более разумный диапазон
                current_time = django_timezone.now().timestamp() * 1000
                hours_back = max(1, (current_time - min_timestamp) / (1000 * 3600))  # часы назад
                # Polygon: ~1800 блоков в час (блок каждые 2 секунды)
                estimated_blocks = min(10000, int(hours_back * 1800) + 100)  # +100 блоков запаса
                min_block = max(0, latest_block - estimated_blocks)
                scan_to_block = latest_block
                logger.info(f"Optimized scan: {hours_back:.1f} hours back, scanning {estimated_blocks} blocks")
            else:
                # Без timestamp ограничиваем разумным диапазоном
                min_block = max(0, latest_block - 2000)  # ~1 час истории
                scan_to_block = latest_block
                logger.info(f"Default scan: last 2000 blocks")
            
            logger.info(f"Scanning Polygon blocks {min_block} to {scan_to_block} for address {address}")
            
            # Эффективное сканирование блоков с ранним завершением
            blocks_checked = 0
            max_blocks_to_check = 2000  # Ограничиваем количество проверяемых блоков
            
            for block_num in range(scan_to_block, min_block, -1):
                if blocks_checked >= max_blocks_to_check:
                    logger.info(f"Reached max blocks limit ({max_blocks_to_check}), stopping scan")
                    break
                    
                try:
                    # Сначала получаем блок без транзакций для проверки timestamp
                    block_header = self.w3.eth.get_block(block_num, full_transactions=False)
                    block_timestamp = block_header.timestamp * 1000
                    
                    # Если блок слишком старый, прекращаем сканирование
                    if block_timestamp < min_timestamp:
                        logger.debug(f"Block {block_num} too old ({block_timestamp} < {min_timestamp}), stopping")
                        break
                    
                    # Если в блоке нет транзакций, пропускаем
                    if not block_header.transactions:
                        continue
                    
                    # Теперь получаем полные транзакции только если блок потенциально интересен
                    block = self.w3.eth.get_block(block_num, full_transactions=True)
                    blocks_checked += 1
                    
                    # Проверяем транзакции в блоке
                    for tx in block.transactions:
                        if (tx.to and tx.to.lower() == checksum_address.lower() and 
                            tx.value > 0):
                            
                            transaction_data = {
                                'transaction_id': tx.hash.hex(),
                                'from_address': tx['from'] if tx['from'] else '',
                                'to_address': tx.to,
                                'value': str(tx.value),  # В Wei
                                'block_number': block_num,
                                'timestamp': block_timestamp,
                                'memo': ''  # POL не поддерживает memo
                            }
                            transactions.append(transaction_data)
                            logger.info(f"Found POL transaction: {tx.hash.hex()} for {Web3.from_wei(tx.value, 'ether')} POL")
                
                except Exception as e:
                    # Подавляем конкретные PoA ошибки и прочие несущественные ошибки
                    if any(keyword in str(e).lower() for keyword in ['extradata', 'poa', 'proof of authority']):
                        logger.debug(f"PoA block {block_num} - expected for Polygon")
                    elif "timeout" in str(e).lower() or "connection" in str(e).lower():
                        logger.warning(f"Network issue at block {block_num}: {e}")
                        # При сетевых проблемах делаем короткую паузу и продолжаем
                        import time
                        time.sleep(0.5)
                    else:
                        logger.warning(f"Error processing block {block_num}: {e}")
                    continue
                
                # Небольшая пауза для снижения нагрузки на RPC
                if blocks_checked % 50 == 0:
                    import time
                    time.sleep(0.05)
            
            logger.info(f"Found {len(transactions)} POL transactions for {address} (checked {blocks_checked} blocks)")
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to get Polygon transactions for {address}: {e}")
            return []

    def send_transaction(self, private_key: str, to_address: str, amount: Decimal, memo: str = "") -> str:
        """
        Send POL transaction.
        
        :param private_key: Sender's private key
        :param to_address: Recipient address
        :param amount: Amount in POL
        :param memo: Not used for POL (native transactions)
        :return: Transaction hash
        """
        try:
            if not is_address(to_address):
                raise PolygonError(f"Invalid recipient address: {to_address}")
            
            # Создаем аккаунт из приватного ключа
            account = Account.from_key(private_key)
            from_address = account.address
            
            # Конвертируем amount в Wei
            amount_wei = Web3.to_wei(amount, 'ether')
            
            # Получаем текущую цену газа
            gas_price = self._get_gas_price()
            
            # Подготавливаем транзакцию
            transaction = {
                'to': to_checksum_address(to_address),
                'value': amount_wei,
                'gas': self.gas_limit,
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(from_address),
                'chainId': self.w3.eth.chain_id
            }
            
            # Подписываем транзакцию
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            
            # Отправляем транзакцию
            try:
                # Попробуем новый формат (web3.py >= 6.0)
                tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            except AttributeError:
                # Обратная совместимость с web3.py < 6.0
                tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            logger.info(f"Sent POL transaction: {tx_hash_hex} ({amount} POL from {from_address} to {to_address})")
            return tx_hash_hex
            
        except Exception as e:
            logger.error(f"Failed to send Polygon transaction: {e}")
            raise PolygonError(f"Transaction failed: {e}")

    def _get_gas_price(self) -> int:
        """Get optimal gas price for the transaction."""
        try:
            # Получаем текущую цену газа
            base_gas_price = self.w3.eth.gas_price
            
            # Применяем множитель
            adjusted_gas_price = int(base_gas_price * self.gas_price_multiplier)
            
            # Ограничиваем максимальной ценой
            final_gas_price = min(adjusted_gas_price, self.max_gas_price)
            
            logger.debug(f"Gas price: base={base_gas_price}, adjusted={adjusted_gas_price}, final={final_gas_price}")
            return final_gas_price
            
        except Exception as e:
            logger.warning(f"Failed to get gas price, using default: {e}")
            return self.max_gas_price

    def is_transaction_confirmed(self, tx_hash: str, required_confirmations: int = 12) -> bool:
        """
        Check if transaction is confirmed with required number of confirmations.
        
        :param tx_hash: Transaction hash
        :param required_confirmations: Number of required confirmations
        :return: True if confirmed
        """
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            if receipt is None:
                return False
            
            current_block = self.w3.eth.block_number
            confirmations = current_block - receipt.blockNumber
            
            is_confirmed = confirmations >= required_confirmations
            logger.debug(f"Transaction {tx_hash}: {confirmations} confirmations (required: {required_confirmations})")
            
            return is_confirmed
            
        except Exception as e:
            logger.warning(f"Failed to check transaction confirmation for {tx_hash}: {e}")
            return False