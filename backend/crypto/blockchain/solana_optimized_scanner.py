"""
Оптимизированный сканер для Solana с параллельной обработкой
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

from solders.pubkey import Pubkey
from solders.signature import Signature

logger = logging.getLogger(__name__)


@dataclass
class SolanaScanResult:
    """Результат сканирования адресов Solana"""
    address: str
    transactions: List[Dict[str, Any]]
    scan_time: float
    error: Optional[str] = None


@dataclass
class SolanaOptimizedScanConfig:
    """Конфигурация оптимизированного сканирования Solana"""
    max_workers: int = 10  # Количество параллельных потоков
    batch_size: int = 20   # Размер пачки адресов
    max_signatures_per_scan: int = 50  # Максимум подписей за одно сканирование
    cache_duration: int = 300  # Время кэширования в секундах
    retry_attempts: int = 3  # Количество попыток при ошибке
    timeout_per_request: float = 30.0  # Таймаут на запрос в секундах


class SolanaOptimizedScanner:
    """
    Оптимизированный сканер Solana с параллельной обработкой
    """
    
    def __init__(self, solana_service, config: SolanaOptimizedScanConfig = None):
        self.service = solana_service
        self.config = config or SolanaOptimizedScanConfig()
        self._cache = {}
        self._cache_lock = threading.RLock()
        self._stats = {
            'addresses_scanned': 0,
            'transactions_found': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0,
            'total_time': 0.0
        }
    
    def _is_cache_valid(self, cache_entry: dict) -> bool:
        """Проверяет валидность кэша"""
        return (time.time() - cache_entry['timestamp']) < self.config.cache_duration
    
    def _get_from_cache(self, address: str, min_timestamp: int) -> Optional[List[Dict[str, Any]]]:
        """Получает данные из кэша"""
        with self._cache_lock:
            cache_key = f"address_{address}_{min_timestamp}"
            if cache_key in self._cache:
                entry = self._cache[cache_key]
                if self._is_cache_valid(entry):
                    self._stats['cache_hits'] += 1
                    return entry['transactions']
                else:
                    del self._cache[cache_key]
            
            self._stats['cache_misses'] += 1
            return None
    
    def _save_to_cache(self, address: str, min_timestamp: int, transactions: List[Dict[str, Any]]):
        """Сохраняет данные в кэш"""
        with self._cache_lock:
            cache_key = f"address_{address}_{min_timestamp}"
            self._cache[cache_key] = {
                'transactions': transactions,
                'timestamp': time.time()
            }
    
    def _scan_single_address(self, address: str, min_timestamp: int = 0) -> SolanaScanResult:
        """Сканирует один адрес Solana"""
        start_time = time.time()
        
        try:
            # Проверяем кэш
            cached_transactions = self._get_from_cache(address, min_timestamp)
            if cached_transactions is not None:
                scan_time = time.time() - start_time
                return SolanaScanResult(
                    address=address,
                    transactions=cached_transactions,
                    scan_time=scan_time
                )
            
            # Получаем подписи для адреса
            try:
                pubkey = Pubkey.from_string(address)
                signatures = self.service.client.get_signatures_for_address(
                    pubkey, 
                    limit=self.config.max_signatures_per_scan
                ).value
                
                if not signatures:
                    # Сохраняем пустой результат в кэш
                    self._save_to_cache(address, min_timestamp, [])
                    scan_time = time.time() - start_time
                    return SolanaScanResult(
                        address=address,
                        transactions=[],
                        scan_time=scan_time
                    )
            except Exception as e:
                return SolanaScanResult(
                    address=address,
                    transactions=[],
                    scan_time=time.time() - start_time,
                    error=f"Failed to get signatures: {e}"
                )
            
            transactions = []
            
            # Обрабатываем подписи
            for sig_info in signatures:
                try:
                    # Проверяем timestamp
                    block_time = getattr(sig_info, "block_time", None)
                    if block_time is not None and min_timestamp and block_time < min_timestamp // 1000:
                        continue
                    
                    # Получаем транзакцию
                    tx_resp = self.service.client.get_transaction(
                        sig_info.signature,
                        max_supported_transaction_version=0
                    ).value
                    
                    if tx_resp is None:
                        continue

                    # transaction_with_meta
                    transaction_with_meta = getattr(tx_resp, "transaction", None)
                    if transaction_with_meta is None:
                        continue

                    # meta
                    meta = getattr(transaction_with_meta, "meta", None)
                    if meta is not None and hasattr(meta, "value"):
                        meta = meta.value  # если Some(...)
                    if meta is None:
                        continue

                    # transaction (UiTransaction)
                    tx_json = getattr(transaction_with_meta, "transaction", None)
                    if tx_json is not None and hasattr(tx_json, "value"):
                        tx_json = tx_json.value  # если Json(...)
                    if tx_json is None:
                        continue

                    # message
                    message = getattr(tx_json, "message", None)
                    if message is not None and hasattr(message, "value"):
                        message = message.value  # если Raw(...)
                    if message is None:
                        continue

                    account_keys = getattr(message, "account_keys", [])
                    pre_balances = getattr(meta, "pre_balances", [])
                    post_balances = getattr(meta, "post_balances", [])

                    for i, acc in enumerate(account_keys):
                        if str(acc) == address:
                            diff = post_balances[i] - pre_balances[i]
                            if diff > 0:
                                # Конвертируем lamports в SOL (1 SOL = 1_000_000_000 lamports)
                                amount_sol = Decimal(diff) / Decimal(1_000_000_000)
                                transaction_data = {
                                    "transaction_id": str(sig_info.signature),
                                    "from_address": str(account_keys[0]),
                                    "to_address": address,
                                    "value": str(amount_sol),  # Возвращаем значение в SOL
                                    "memo": None,
                                    "block_time": block_time
                                }
                                transactions.append(transaction_data)
                except Exception as e:
                    logger.warning(f"Error processing signature {sig_info.signature} for address {address}: {e}")
                    continue
            
            # Сохраняем результаты в кэш
            self._save_to_cache(address, min_timestamp, transactions)
            
            scan_time = time.time() - start_time
            return SolanaScanResult(
                address=address,
                transactions=transactions,
                scan_time=scan_time
            )
            
        except Exception as e:
            scan_time = time.time() - start_time
            logger.error(f"Error scanning address {address}: {e}")
            return SolanaScanResult(
                address=address,
                transactions=[],
                scan_time=scan_time,
                error=str(e)
            )
    
    def scan_optimized(self, addresses: List[str], min_timestamp: int = 0) -> List[Dict[str, Any]]:
        """
        Оптимизированное параллельное сканирование адресов Solana
        """
        start_time = time.time()
        all_transactions = []
        
        logger.info(f"Starting optimized Solana scan for {len(addresses)} addresses")
        
        # Разбиваем адреса на батчи
        batches = [addresses[i:i + self.config.batch_size] for i in range(0, len(addresses), self.config.batch_size)]
        
        for batch_idx, batch in enumerate(batches):
            logger.info(f"Processing batch {batch_idx + 1}/{len(batches)} with {len(batch)} addresses")
            
            # Сканируем адреса параллельно
            with ThreadPoolExecutor(max_workers=min(self.config.max_workers, len(batch))) as executor:
                # Создаем задачи
                future_to_address = {
                    executor.submit(self._scan_single_address, address, min_timestamp): address 
                    for address in batch
                }
                
                # Собираем результаты
                for future in as_completed(future_to_address):
                    address = future_to_address[future]
                    try:
                        result = future.result(timeout=self.config.timeout_per_request)
                        if result.error:
                            logger.error(f"Error scanning {address}: {result.error}")
                            continue
                        
                        # Добавляем найденные транзакции
                        all_transactions.extend(result.transactions)
                        self._stats['transactions_found'] += len(result.transactions)
                        
                    except Exception as e:
                        logger.error(f"Error processing result for {address}: {e}")
                        continue
            
            # Пауза между батчами
            if batch_idx < len(batches) - 1:
                time.sleep(0.1)
        
        total_time = time.time() - start_time
        self._stats['total_time'] += total_time
        self._stats['addresses_scanned'] += len(addresses)
        
        logger.info(f"Optimized Solana scan completed: {len(all_transactions)} transactions found in {total_time:.2f}s")
        return all_transactions
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику сканирования"""
        return self._stats.copy()