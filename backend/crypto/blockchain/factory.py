from .base import BaseBlockchainService
from .tron import TronService
from .bitcoin import BitcoinService

def get_blockchain_service(network: str) -> BaseBlockchainService:
    """
    Factory function to get the appropriate blockchain service based on the network.
    """
    network_lower = network.lower()

    if network_lower in ['trc20', 'tron']:
        return TronService(network='nile') # or 'mainnet' based on settings
    elif network_lower in ['btc', 'bitcoin']:
        return BitcoinService(network='mainnet') # or 'testnet'
    # Add other services here, e.g., for Ethereum
    # elif network_lower in ['erc20', 'ethereum']:
    #     return EthereumService()
    else:
        raise ValueError(f"Unsupported blockchain network: {network}")
