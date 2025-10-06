import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from crypto.blockchain.factory import get_blockchain_service
from crypto.models import UserWallet

def test_transaction_detection():
    # Get the wallet
    wallet = UserWallet.objects.get(deposit_address='5s9HUwUzaDWtJvGCuSns31QGgr8PLqdocuuGk4bkaBZK')
    print(f"Checking transactions for wallet: {wallet.deposit_address}")
    
    # Get blockchain service
    service = get_blockchain_service('solana')
    
    # Get transactions
    transactions = service.get_transactions(wallet.deposit_address)
    print(f"Found {len(transactions)} transactions")
    
    # Print details of first few transactions
    for i, tx in enumerate(transactions[:5]):
        print(f"{i+1}. Tx Hash: {tx.get('transaction_id')}")
        print(f"   Amount: {tx.get('value')}")
        print(f"   From: {tx.get('from_address')}")
        print(f"   To: {tx.get('to_address')}")
        print()

if __name__ == "__main__":
    test_transaction_detection()