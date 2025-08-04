from django.conf import settings
from .base import BaseBlockchainService
from .tron import TronService
from .bitcoin import BitcoinService
from .xrp import XRPService
from .ethereum import EthereumService

def get_blockchain_service(network: str, address: str = None) -> BaseBlockchainService:
    """
    Factory function to get the appropriate blockchain service.
    It can determine the service by network name or by address format.
    """
    # Определение по формату адреса, если он предоставлен
    if address:
        if address.startswith('T') and len(address) == 34:
            return TronService()
        elif address.startswith('0x') and len(address) == 42:
            eth_network = getattr(settings, 'ETHEREUM_NETWORK', 'goerli')
            return EthereumService(network=eth_network)
        elif address.startswith('bc1') or address.startswith('tb1'):
             return BitcoinService(network='testnet' if address.startswith('tb1') else 'mainnet')
        elif address.startswith('r') and len(address) > 25:
            return XRPService(network='mainnet') # Упрощено для примера

    # Определение по имени сети (как было раньше)
    network_lower = network.lower() if network else ''
    if network_lower in ['trc20', 'tron']:
        return TronService()
    elif network_lower in ['btc', 'bitcoin']:
        return BitcoinService(network='testnet')
    elif network_lower in ['erc20', 'ethereum', 'eth']:
        eth_network = getattr(settings, 'ETHEREUM_NETWORK', 'goerli')
        return EthereumService(network=eth_network)
    elif network_lower in ['xrp', 'ripple']:
        return XRPService(network='testnet')
    
    raise ValueError(f"Unsupported blockchain network: {network} or address format.")
