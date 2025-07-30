from django.conf import settings
from .base import BaseBlockchainService
from .tron import TronService
from .bitcoin import BitcoinService
from .xrp import XRPService
from .ethereum import EthereumService

def get_blockchain_service(network: str) -> BaseBlockchainService:
    """
    Factory function to get the appropriate blockchain service based on the network.
    """
    network_lower = network.lower()

    if network_lower in ['trc20', 'tron']:
        return TronService()
    elif network_lower in ['btc', 'bitcoin']:
        # Временно используем testnet для разработки
        btc_network = 'testnet'
        return BitcoinService(network=btc_network)
    elif network_lower in ['erc20', 'ethereum', 'eth']:
        # Используем сеть из настроек
        eth_network = getattr(settings, 'ETHEREUM_NETWORK', 'goerli')
        return EthereumService(network=eth_network)
    elif network_lower in ['xrp', 'ripple']:
        return XRPService(network='mainnet' if 'main' in network_lower else 'testnet')
    else:
        raise ValueError(f"Unsupported blockchain network: {network}")
