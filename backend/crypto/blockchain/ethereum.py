"""Utility functions for interacting with Ethereum blockchain (ERC20 deposits)."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import List, Dict, Any
import json
import requests
from web3 import Web3
from eth_account import Account

logger = logging.getLogger(__name__)

# Ethereum configuration
ETHEREUM_RPC_URL = os.getenv("ETHEREUM_RPC_URL", "https://mainnet.infura.io/v3/your-project-id")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
ETHEREUM_NETWORK = os.getenv("ETHEREUM_NETWORK", "mainnet")  # mainnet, sepolia, goerli

# USDT contract address on Ethereum (ERC20)
USDT_CONTRACT_ADDRESS = "0xdAC17F958D2ee523a2206206994597C13D831ec7"  # Mainnet USDT

# ABI for ERC20 token transfers (Transfer event)
ERC20_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "name": "from",
                "type": "address"
            },
            {
                "indexed": True,
                "name": "to",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "value",
                "type": "uint256"
            }
        ],
        "name": "Transfer",
        "type": "event"
    }
]


class EthereumError(RuntimeError):
    """Raised when Ethereum API returns an error."""


def _get_web3() -> Web3:
    """Get Web3 instance with proper configuration."""
    w3 = Web3(Web3.HTTPProvider(ETHEREUM_RPC_URL))
    if not w3.is_connected():
        raise EthereumError(f"Cannot connect to Ethereum RPC: {ETHEREUM_RPC_URL}")
    return w3


def _get_etherscan_url() -> str:
    """Get Etherscan API URL based on network."""
    if ETHEREUM_NETWORK == "sepolia":
        return "https://api-sepolia.etherscan.io/api"
    elif ETHEREUM_NETWORK == "goerli":
        return "https://api-goerli.etherscan.io/api"
    else:  # mainnet
        return "https://api.etherscan.io/api"


def get_erc20_transfers(address: str, min_timestamp: int) -> List[Dict[str, Any]]:
    """Fetches ERC20 transfers to *address* after *min_timestamp* (ms).

    Args:
        address: Ethereum address (checksum).
        min_timestamp: minimal block timestamp (milliseconds since epoch).

    Returns:
        List of raw transfer dicts (Etherscan format).
    """
    if not ETHERSCAN_API_KEY:
        raise EthereumError("ETHERSCAN_API_KEY is required for ERC20 transfers")
    
    url = _get_etherscan_url()
    params = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": USDT_CONTRACT_ADDRESS,
        "address": address,
        "starttime": min_timestamp // 1000,  # Convert to seconds
        "sort": "asc",
        "apikey": ETHERSCAN_API_KEY
    }
    
    try:
        resp = requests.get(url, params=params, headers={"Accept": "application/json"}, timeout=20)
        
        if resp.status_code != 200:
            logger.error(f"Etherscan HTTP error {resp.status_code}: {resp.text}")
            raise EthereumError(f"Etherscan HTTP {resp.status_code}: {resp.text}")
            
        data = resp.json()
        
        if data.get("status") != "1":
            logger.error(f"Etherscan API error: {data}")
            raise EthereumError(str(data))

        transfers = []
        for item in data.get("result", []):
            # Convert Etherscan format to our internal format
            transfer = {
                "transaction_id": item.get("hash"),
                "from": item.get("from"),
                "to": item.get("to"),
                "value": item.get("value"),
                "block_timestamp": int(item.get("timeStamp", 0)) * 1000,  # Convert to milliseconds
                "token_info": {
                    "symbol": item.get("tokenSymbol"),
                    "decimals": int(item.get("tokenDecimal", 6)),
                    "name": item.get("tokenName")
                },
                "type": "Transfer",
                "memo": ""  # Ethereum doesn't have memo like TRC20, we'll use input data
            }
            
            # Try to extract memo from transaction input data
            try:
                w3 = _get_web3()
                tx = w3.eth.get_transaction(item.get("hash"))
                if tx and tx.get("input") and tx["input"] != "0x":
                    # Check if input data contains memo (this is a simplified approach)
                    input_data = tx["input"]
                    if len(input_data) > 10:  # More than just function selector
                        # Try to decode as string (this is a basic approach)
                        try:
                            # Remove function selector and try to decode as string
                            data_part = input_data[10:]  # Remove 0x and 4 bytes function selector
                            if len(data_part) >= 64:  # At least one parameter
                                # This is a simplified approach - in real implementation you'd need proper ABI decoding
                                memo = w3.to_text(hexstr=data_part[:64])
                                if memo and memo.strip():
                                    transfer["memo"] = memo.strip()
                        except Exception as e:
                            logger.debug(f"Could not decode memo from input data: {e}")
            except Exception as e:
                logger.debug(f"Could not fetch transaction details for memo extraction: {e}")
            
            transfers.append(transfer)
            
        logger.info(f"[get_erc20_transfers] Found {len(transfers)} transfers for address {address}")
        return transfers

    except requests.Timeout:
        logger.error("Request to Etherscan timed out")
        raise EthereumError("Etherscan request timed out")
    except requests.RequestException as e:
        logger.error(f"Request to Etherscan failed: {e}")
        raise EthereumError(f"Etherscan request failed: {e}")


def extract_deposit_events(transfers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Converts raw transfers to simplified deposit events."""
    events: List[Dict[str, Any]] = []
    for item in transfers:
        # For Ethereum, we'll use a different approach for memo
        # Since Ethereum doesn't have built-in memo like TRC20, we'll use the transaction input data
        memo = item.get("memo", "")
        
        # For now, we'll accept transactions without memo (you might want to change this)
        # In a real implementation, you might want to require some form of identification
        if not memo:
            logger.info(f"[extract_deposit_events] No memo found for transaction {item.get('transaction_id')}")
            # You can either skip these or handle them differently
            continue
            
        value_raw = int(item["value"])
        decimals = int(item["token_info"].get("decimals", 6))
        amount = value_raw / (10 ** decimals)
        
        events.append({
            "tx_hash": item["transaction_id"],
            "amount": amount,
            "memo": memo,
            "timestamp": datetime.fromtimestamp(item["block_timestamp"] / 1000, tz=timezone.utc).isoformat(),
        })
    
    logger.info(f"[extract_deposit_events] Extracted events: {json.dumps(events, indent=2)}")
    return events


def get_ethereum_balance(address: str) -> float:
    """Get ETH balance for an address."""
    try:
        w3 = _get_web3()
        balance_wei = w3.eth.get_balance(address)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        return float(balance_eth)
    except Exception as e:
        logger.error(f"Error getting ETH balance for {address}: {e}")
        raise EthereumError(f"Failed to get ETH balance: {e}")


def get_erc20_balance(address: str, contract_address: str) -> float:
    """Get ERC20 token balance for an address."""
    try:
        w3 = _get_web3()
        contract = w3.eth.contract(address=contract_address, abi=ERC20_ABI)
        balance = contract.functions.balanceOf(address).call()
        # Note: You'll need to get decimals from the contract or hardcode for known tokens
        decimals = 6  # For USDT
        return balance / (10 ** decimals)
    except Exception as e:
        logger.error(f"Error getting ERC20 balance for {address}: {e}")
        raise EthereumError(f"Failed to get ERC20 balance: {e}") 