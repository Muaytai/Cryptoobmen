"""Blockchain provider factory and common helpers."""
from importlib import import_module
from typing import Dict, Type

from .base import BlockchainProvider

# Map network key -> provider class dotted path
PROVIDER_REGISTRY: Dict[str, str] = {
    "tron": "backend.blockchain.tron_provider.TronProvider",
    # "bitcoin": "backend.blockchain.bitcoin_provider.BitcoinProvider",
    # "evm": "backend.blockchain.evm_provider.EvmProvider",
}


def get_provider(network: str) -> BlockchainProvider:
    """Return provider instance for given network key (e.g. 'tron')."""
    if network not in PROVIDER_REGISTRY:
        raise ValueError(f"No provider configured for network '{network}'")

    dotted_path = PROVIDER_REGISTRY[network]
    module_path, class_name = dotted_path.rsplit(".", 1)
    module = import_module(module_path)
    cls: Type[BlockchainProvider] = getattr(module, class_name)
    return cls()
