#!/usr/bin/env python3
"""
Utility script to generate a Bitcoin testnet wallet for system use.

Usage:
    python backend/scripts/generate_testnet_btc_wallet.py

Outputs legacy (m/n) and SegWit (tb1) deposit addresses plus the WIF private key.
"""

from bit import PrivateKeyTestnet


def main() -> None:
    key = PrivateKeyTestnet()

    print("=== Bitcoin Testnet Wallet ===")
    print(f"Legacy address  : {key.address}")
    try:
        segwit_address = key.segwit_address
    except AttributeError:
        segwit_address = None

    if segwit_address:
        print(f"SegWit address  : {segwit_address}")

    print(f"Private key (WIF): {key.to_wif()}")
    print("\nStore the private key securely. In dev you can copy it to the system wallet.")


if __name__ == "__main__":
    main()

