import pytest
from unittest.mock import Mock, patch
from decimal import Decimal
from crypto.blockchain.solana import SolanaService
from crypto.blockchain.solana_optimized_scanner import SolanaOptimizedScanner, SolanaOptimizedScanConfig

@pytest.fixture
def solana_service():
    """Создает мок для Solana сервиса"""
    with patch('crypto.blockchain.solana.Client') as mock_client:
        service = SolanaService(network='devnet')
        service.client = mock_client
        return service

@pytest.fixture
def optimized_scanner(solana_service):
    """Создает оптимизированный сканер"""
    config = SolanaOptimizedScanConfig(
        max_workers=2,
        batch_size=5,
        max_signatures_per_scan=10,
        cache_duration=60
    )
    return SolanaOptimizedScanner(solana_service, config)

def test_solana_optimized_scanner_initialization(solana_service):
    """Проверяет инициализацию оптимизированного сканера"""
    scanner = SolanaOptimizedScanner(solana_service)
    assert scanner.service == solana_service
    assert scanner.config.max_workers == 10  # Значение по умолчанию
    assert scanner.config.batch_size == 20   # Значение по умолчанию

def test_solana_optimized_scanner_with_custom_config(solana_service):
    """Проверяет инициализацию сканера с кастомной конфигурацией"""
    config = SolanaOptimizedScanConfig(
        max_workers=5,
        batch_size=10,
        max_signatures_per_scan=25
    )
    scanner = SolanaOptimizedScanner(solana_service, config)
    assert scanner.config.max_workers == 5
    assert scanner.config.batch_size == 10
    assert scanner.config.max_signatures_per_scan == 25

@pytest.mark.django_db
def test_scan_optimized_empty_addresses(solana_service, optimized_scanner):
    """Проверяет сканирование пустого списка адресов"""
    result = optimized_scanner.scan_optimized([])
    assert result == []
    assert isinstance(result, list)

# Дополнительные тесты могут быть добавлены для проверки реальной функциональности
# когда будет доступна тестовая среда Solana