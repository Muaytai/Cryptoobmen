"""
Утилиты для группировки RPC запросов в батчи для повышения эффективности
"""
import logging
from typing import List, Dict, Any, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import time
from decimal import Decimal

logger = logging.getLogger(__name__)


class BatchRPCProcessor:
    """Процессор для группировки и выполнения RPC запросов батчами"""
    
    def __init__(self, max_workers: int = 8, batch_size: int = 20):
        self.max_workers = max_workers
        self.batch_size = batch_size
    
    def batch_get_balances(self, service, addresses: List[str]) -> Dict[str, Decimal]:
        """
        Получает балансы для множества адресов параллельно
        
        :param service: Сервис блокчейна
        :param addresses: Список адресов
        :return: Словарь {адрес: баланс}
        """
        balances = {}
        
        # Разбиваем адреса на батчи
        batches = [addresses[i:i + self.batch_size] for i in range(0, len(addresses), self.batch_size)]
        
        logger.info(f"[BATCH] Processing {len(addresses)} addresses in {len(batches)} batches")
        
        for batch_idx, batch in enumerate(batches):
            logger.info(f"[BATCH] Processing batch {batch_idx + 1}/{len(batches)} with {len(batch)} addresses")
            
            with ThreadPoolExecutor(max_workers=min(self.max_workers, len(batch))) as executor:
                # Запускаем параллельные запросы для батча
                future_to_address = {
                    executor.submit(self._safe_get_balance, service, addr): addr 
                    for addr in batch
                }
                
                # Собираем результаты
                for future in as_completed(future_to_address):
                    address = future_to_address[future]
                    try:
                        balance = future.result(timeout=30)
                        balances[address] = balance
                    except Exception as e:
                        logger.error(f"[BATCH] Error getting balance for {address}: {e}")
                        balances[address] = Decimal('0')
            
            # Небольшая пауза между батчами для снижения нагрузки
            if batch_idx < len(batches) - 1:
                time.sleep(0.1)
        
        logger.info(f"[BATCH] Completed balance requests for {len(balances)} addresses")
        return balances
    
    def batch_get_transactions(self, service, addresses_with_params: List[Tuple[str, Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Получает транзакции для множества адресов параллельно
        
        :param service: Сервис блокчейна
        :param addresses_with_params: Список кортежей (адрес, параметры_запроса)
        :return: Словарь {адрес: список_транзакций}
        """
        transactions = {}
        
        # Разбиваем запросы на батчи
        batches = [addresses_with_params[i:i + self.batch_size] for i in range(0, len(addresses_with_params), self.batch_size)]
        
        logger.info(f"[BATCH] Processing transactions for {len(addresses_with_params)} addresses in {len(batches)} batches")
        
        for batch_idx, batch in enumerate(batches):
            logger.info(f"[BATCH] Processing transaction batch {batch_idx + 1}/{len(batches)} with {len(batch)} requests")
            
            with ThreadPoolExecutor(max_workers=min(self.max_workers, len(batch))) as executor:
                # Запускаем параллельные запросы для батча
                future_to_address = {
                    executor.submit(self._safe_get_transactions, service, addr, params): addr 
                    for addr, params in batch
                }
                
                # Собираем результаты
                for future in as_completed(future_to_address):
                    address = future_to_address[future]
                    try:
                        txs = future.result(timeout=60)
                        transactions[address] = txs
                    except Exception as e:
                        logger.error(f"[BATCH] Error getting transactions for {address}: {e}")
                        transactions[address] = []
            
            # Пауза между батчами
            if batch_idx < len(batches) - 1:
                time.sleep(0.2)
        
        logger.info(f"[BATCH] Completed transaction requests for {len(transactions)} addresses")
        return transactions
    
    def _safe_get_balance(self, service, address: str) -> Decimal:
        """Безопасное получение баланса с обработкой ошибок"""
        try:
            return service.get_balance(address)
        except Exception as e:
            logger.warning(f"[BATCH] Failed to get balance for {address}: {e}")
            return Decimal('0')
    
    def _safe_get_transactions(self, service, address: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Безопасное получение транзакций с обработкой ошибок"""
        try:
            return service.get_transactions(address=address, **params)
        except Exception as e:
            logger.warning(f"[BATCH] Failed to get transactions for {address}: {e}")
            return []


class CachedBatchProcessor(BatchRPCProcessor):
    """Батч-процессор с дополнительным кэшированием"""
    
    def __init__(self, max_workers: int = 8, batch_size: int = 20, cache_duration: int = 30):
        super().__init__(max_workers, batch_size)
        self.cache_duration = cache_duration
        self._balance_cache = {}
        self._transaction_cache = {}
    
    @lru_cache(maxsize=500)
    def _get_cached_balance_key(self, service_name: str, address: str, timestamp_window: int) -> str:
        """Генерирует ключ кэша для баланса"""
        return f"{service_name}:{address}:{timestamp_window}"
    
    def get_cached_balance(self, service, address: str) -> Decimal:
        """Получает баланс с кэшированием"""
        service_name = service.__class__.__name__
        current_time = int(time.time())
        cache_window = current_time // self.cache_duration
        cache_key = self._get_cached_balance_key(service_name, address, cache_window)
        
        if cache_key in self._balance_cache:
            return self._balance_cache[cache_key]
        
        try:
            balance = service.get_balance(address)
            self._balance_cache[cache_key] = balance
            return balance
        except Exception as e:
            logger.error(f"[CACHED_BATCH] Error getting balance for {address}: {e}")
            return Decimal('0')
    
    def batch_get_balances_cached(self, service, addresses: List[str]) -> Dict[str, Decimal]:
        """Получает балансы с использованием кэша"""
        balances = {}
        uncached_addresses = []
        
        # Проверяем кэш
        service_name = service.__class__.__name__
        current_time = int(time.time())
        cache_window = current_time // self.cache_duration
        
        for address in addresses:
            cache_key = self._get_cached_balance_key(service_name, address, cache_window)
            if cache_key in self._balance_cache:
                balances[address] = self._balance_cache[cache_key]
            else:
                uncached_addresses.append(address)
        
        logger.info(f"[CACHED_BATCH] Found {len(balances)} cached balances, need to fetch {len(uncached_addresses)}")
        
        # Получаем недостающие балансы
        if uncached_addresses:
            new_balances = self.batch_get_balances(service, uncached_addresses)
            
            # Сохраняем в кэш
            for addr, balance in new_balances.items():
                cache_key = self._get_cached_balance_key(service_name, addr, cache_window)
                self._balance_cache[cache_key] = balance
                balances[addr] = balance
        
        return balances
    
    def cleanup_cache(self):
        """Очищает устаревшие записи кэша"""
        current_time = int(time.time())
        cutoff_time = current_time - (self.cache_duration * 3)  # Удаляем записи старше 3 интервалов
        
        # Очищаем balance cache
        keys_to_remove = []
        for key in self._balance_cache.keys():
            try:
                *_, timestamp_str = key.split(':')
                if int(timestamp_str) < cutoff_time // self.cache_duration:
                    keys_to_remove.append(key)
            except (ValueError, IndexError):
                keys_to_remove.append(key)  # Удаляем некорректные ключи
        
        for key in keys_to_remove:
            del self._balance_cache[key]
        
        if keys_to_remove:
            logger.info(f"[CACHED_BATCH] Cleaned up {len(keys_to_remove)} expired cache entries")


# Глобальные экземпляры для использования в задачах
batch_processor = BatchRPCProcessor(max_workers=10, batch_size=25)
cached_batch_processor = CachedBatchProcessor(max_workers=10, batch_size=25, cache_duration=60)
