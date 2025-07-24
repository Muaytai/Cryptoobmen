from django.conf import settings
from .base import BaseBlockchainService
from .tron import TronService
from .bitcoin import BitcoinService
from .xrp import XRPService

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
    # Add other services here, e.g., for Ethereum
    # elif network_lower in ['erc20', 'ethereum']:
    #     return EthereumService()
    elif network_lower in ['xrp', 'ripple']:
        return XRPService(network='mainnet' if 'main' in network_lower else 'testnet')
    else:
        raise ValueError(f"Unsupported blockchain network: {network}")
