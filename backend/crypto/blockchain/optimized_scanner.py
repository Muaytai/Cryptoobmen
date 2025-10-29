"""
Оптимизированный сканер блокчейна с параллельной обработкой
"""
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime, timedelta
import time
import threading
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    """Результат сканирования блока"""
    block_number: int
    transactions: List[Dict[str, Any]]
    scan_time: float
    error: Optional[str] = None


@dataclass
class OptimizedScanConfig:
    """Конфигурация оптимизированного сканирования"""
    max_workers: int = 10  # Количество параллельных потоков
    batch_size: int = 50   # Размер пачки блоков
    max_blocks_per_scan: int = 1000  # Максимум блоков за одно сканирование
    cache_duration: int = 300  # Время кэширования в секундах
    retry_attempts: int = 3  # Количество попыток при ошибке
    timeout_per_block: float = 30.0  # Таймаут на блок в секундах


class OptimizedBlockchainScanner:
    """
    Оптимизированный сканер блокчейна с параллельной обработкой
    """
    
    def __init__(self, blockchain_service, config: OptimizedScanConfig = None):
        self.service = blockchain_service
        self.config = config or OptimizedScanConfig()
        self._cache = {}
        self._cache_lock = threading.RLock()
        self._stats = {
            'blocks_scanned': 0,
            'transactions_found': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0,
            'total_time': 0.0
        }
    
    def _is_cache_valid(self, cache_entry: dict) -> bool:
        """Проверяет валидность кэша"""
        return (time.time() - cache_entry['timestamp']) < self.config.cache_duration
    
    def _get_from_cache(self, block_number: int) -> Optional[List[Dict[str, Any]]]:
        """Получает данные из кэша"""
        with self._cache_lock:
            cache_key = f"block_{block_number}"
            if cache_key in self._cache:
                entry = self._cache[cache_key]
                if self._is_cache_valid(entry):
                    self._stats['cache_hits'] += 1
                    return entry['transactions']
                else:
                    del self._cache[cache_key]
            
            self._stats['cache_misses'] += 1
            return None
    
    def _save_to_cache(self, block_number: int, transactions: List[Dict[str, Any]]):
        """Сохраняет данные в кэш"""
        with self._cache_lock:
            cache_key = f"block_{block_number}"
            self._cache[cache_key] = {
                'transactions': transactions,
                'timestamp': time.time()
            }
    
    def _scan_single_block(self, block_number: int, addresses: List[str]) -> ScanResult:
        """Сканирует один блок"""
        start_time = time.time()
        
        try:
            # Проверяем кэш
            cached_transactions = self._get_from_cache(block_number)
            if cached_transactions is not None:
                # Фильтруем кэшированные транзакции по нужным адресам
                filtered_transactions = [
                    tx for tx in cached_transactions 
                    if any(addr.lower() in tx.get('to', '').lower() for addr in addresses)
                ]
                
                scan_time = time.time() - start_time
                return ScanResult(
                    block_number=block_number,
                    transactions=filtered_transactions,
                    scan_time=scan_time
                )
            
            # Получаем блок
            try:
                block = self.service.w3.eth.get_block(block_number, full_transactions=True)
            except Exception as e:
                return ScanResult(
                    block_number=block_number,
                    transactions=[],
                    scan_time=time.time() - start_time,
                    error=f"Failed to get block: {e}"
                )
            
            transactions = []
            block_transactions = block.get('transactions', [])
            
            # Фильтруем транзакции по адресам
            for tx in block_transactions:
                tx_to = tx.get('to', '').lower() if tx.get('to') else ''
                
                # Проверяем входящие транзакции
                for address in addresses:
                    if tx_to == address.lower():
                        # Проверяем что это обычная POL транзакция (не контракт)
                        if tx.get('value', 0) > 0:
                            amount_wei = tx.get('value', 0)
                            amount_pol = self.service.w3.from_wei(amount_wei, 'ether')
                            
                            transaction_data = {
                                'transaction_id': tx['hash'].hex(),
                                'value': str(amount_pol),
                                'to_address': tx_to,
                                'from_address': tx.get('from', '').lower(),
                                'block_number': block_number,
                                'timestamp': block.get('timestamp', 0),
                                'gas_used': tx.get('gas', 0),
                                'gas_price': tx.get('gasPrice', 0)
                            }
                            transactions.append(transaction_data)
            
            # Сохраняем все транзакции блока в кэш
            all_block_transactions = []
            for tx in block_transactions:
                if tx.get('value', 0) > 0:
                    amount_wei = tx.get('value', 0)
                    amount_pol = self.service.w3.from_wei(amount_wei, 'ether')
                    all_block_transactions.append({
                        'transaction_id': tx['hash'].hex(),
                        'value': str(amount_pol),
                        'to': tx.get('to', '').lower(),
                        'from': tx.get('from', '').lower(),
                        'block_number': block_number,
                        'timestamp': block.get('timestamp', 0)
                    })
            
            self._save_to_cache(block_number, all_block_transactions)
            
            scan_time = time.time() - start_time
            return ScanResult(
                block_number=block_number,
                transactions=transactions,
                scan_time=scan_time
            )
            
        except Exception as e:
            scan_time = time.time() - start_time
            logger.error(f"Error scanning block {block_number}: {e}")
            return ScanResult(
                block_number=block_number,
                transactions=[],
                scan_time=scan_time,
                error=str(e)
            )
    
    def scan_blocks_parallel(self, addresses: List[str], from_block: int, to_block: int) -> List[Dict[str, Any]]:
        """
        Параллельное сканирование блоков
        """
        start_time = time.time()
        all_transactions = []
        
        # Ограничиваем количество блоков
        total_blocks = to_block - from_block + 1
        if total_blocks > self.config.max_blocks_per_scan:
            to_block = from_block + self.config.max_blocks_per_scan - 1
            logger.warning(f"Limiting scan to {self.config.max_blocks_per_scan} blocks: {from_block}-{to_block}")
        
        logger.info(f"Scanning blocks {from_block}-{to_block} for {len(addresses)} addresses with {self.config.max_workers} workers")
        
        # Создаем список блоков для сканирования
        blocks_to_scan = list(range(from_block, to_block + 1))
        
        # Сканируем блоки параллельно
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Создаем задачи
            future_to_block = {
                executor.submit(self._scan_single_block, block_num, addresses): block_num
                for block_num in blocks_to_scan
            }
            
            # Обрабатываем результаты
            for future in as_completed(future_to_block, timeout=self.config.timeout_per_block * len(blocks_to_scan)):
                try:
                    result = future.result()
                    self._stats['blocks_scanned'] += 1
                    
                    if result.error:
                        self._stats['errors'] += 1
                        logger.warning(f"Block {result.block_number} scan error: {result.error}")
                    else:
                        self._stats['transactions_found'] += len(result.transactions)
                        all_transactions.extend(result.transactions)
                        
                        if result.transactions:
                            logger.debug(f"Block {result.block_number}: {len(result.transactions)} transactions ({result.scan_time:.2f}s)")
                
                except Exception as e:
                    self._stats['errors'] += 1
                    logger.error(f"Future execution error: {e}")
        
        total_time = time.time() - start_time
        self._stats['total_time'] += total_time
        
        logger.info(f"Parallel scan completed: {len(all_transactions)} transactions found in {total_time:.2f}s")
        self._log_stats()
        
        return all_transactions
    
    def scan_optimized(self, addresses: List[str], from_block: int = None, to_block: int = None) -> List[Dict[str, Any]]:
        """
        Оптимизированное сканирование с умными диапазонами
        """
        try:
            current_block = self.service.w3.eth.block_number
            
            # Умные значения по умолчанию
            if to_block is None:
                to_block = current_block
            
            if from_block is None:
                # Сканируем последние 100 блоков для новых депозитов
                from_block = max(current_block - 100, 1)
            
            # Проверяем разумность диапазона
            if to_block < from_block:
                logger.warning(f"Invalid block range: {from_block}-{to_block}")
                return []
            
            # Для больших диапазонов используем батчи
            total_blocks = to_block - from_block + 1
            if total_blocks > self.config.batch_size:
                return self._scan_in_batches(addresses, from_block, to_block)
            else:
                return self.scan_blocks_parallel(addresses, from_block, to_block)
        
        except Exception as e:
            logger.error(f"Optimized scan failed: {e}")
            return []
    
    def _scan_in_batches(self, addresses: List[str], from_block: int, to_block: int) -> List[Dict[str, Any]]:
        """Сканирование большого диапазона батчами"""
        all_transactions = []
        current_from = from_block
        
        while current_from <= to_block:
            current_to = min(current_from + self.config.batch_size - 1, to_block)
            
            logger.info(f"Scanning batch: blocks {current_from}-{current_to}")
            batch_transactions = self.scan_blocks_parallel(addresses, current_from, current_to)
            all_transactions.extend(batch_transactions)
            
            current_from = current_to + 1
            
            # Небольшая пауза между батчами
            time.sleep(0.1)
        
        return all_transactions
    
    def _log_stats(self):
        """Логирует статистику сканирования"""
        stats = self._stats
        if stats['blocks_scanned'] > 0:
            avg_time_per_block = stats['total_time'] / stats['blocks_scanned']
            cache_hit_rate = stats['cache_hits'] / (stats['cache_hits'] + stats['cache_misses']) * 100
            
            logger.info(f"Scan stats: blocks={stats['blocks_scanned']}, "
                       f"transactions={stats['transactions_found']}, "
                       f"errors={stats['errors']}, "
                       f"cache_hit_rate={cache_hit_rate:.1f}%, "
                       f"avg_time_per_block={avg_time_per_block:.2f}s")
    
    def clear_cache(self):
        """Очищает кэш"""
        with self._cache_lock:
            self._cache.clear()
        logger.info("Scanner cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику сканирования"""
        return self._stats.copy()
