import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('D:/PythonProjects/Cryptoobmen/backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from crypto.blockchain.solana import SolanaService
from crypto.models import UserWallet, Cryptocurrency

def test_solana_wallet():
    print("Testing Solana wallet...")
    
    # Get the SOL currency
    crypto = Cryptocurrency.objects.get(symbol='SOL')
    print(f"SOL currency: {crypto}")
    
    # Get the wallet
    wallet = UserWallet.objects.get(currency=crypto, deposit_address='GkVvtMDQ5v1ReiScLQAf45B2X3H1WXr8hrJoY7jcqddQ')
    print(f"Wallet: {wallet}")
    print(f"Balance (DB): {wallet.balance}")
    print(f"Available balance (DB): {wallet.available_balance}")
    
    # Test Solana service
    service = SolanaService()
    print(f"Solana service initialized with network: {service.network}")
    
    # Get real balance
    real_balance = service.get_balance('GkVvtMDQ5v1ReiScLQAf45B2X3H1WXr8hrJoY7jcqddQ')
    print(f"Real balance (Blockchain): {real_balance}")
    
    # Get transactions
    print("Fetching transactions...")
    txs = service.get_transactions('GkVvtMDQ5v1ReiScLQAf45B2X3H1WXr8hrJoY7jcqddQ')
    print(f"Transactions found: {len(txs)}")
    
    # Show first few transactions
    for i, tx in enumerate(txs[:3]):
        print(f"Transaction {i+1}: {tx}")

if __name__ == "__main__":
    test_solana_wallet()