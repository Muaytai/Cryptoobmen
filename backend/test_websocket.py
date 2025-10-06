import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append('d:\\PythonProjects\\Cryptoobmen\\backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from crypto.models import UserWallet, Cryptocurrency
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def test_websocket():
    # Get the first user
    User = get_user_model()
    user = User.objects.first()
    if not user:
        print("No users found. Please create a user first.")
        return
        
    # Get SOL cryptocurrency (get the first one if there are multiple)
    try:
        crypto = Cryptocurrency.objects.filter(symbol='SOL').first()
        if not crypto:
            print("SOL cryptocurrency not found.")
            return
    except Cryptocurrency.DoesNotExist:
        print("SOL cryptocurrency not found.")
        return
        
    # Get or create a wallet for the user
    wallet, created = UserWallet.objects.get_or_create(
        user=user, 
        currency=crypto, 
        defaults={
            'balance': 0, 
            'is_system_wallet': False, 
            'is_active': True
        }
    )
    
    if not wallet.deposit_address:
        print("No deposit address found for wallet.")
        return
        
    print(f"Using wallet address: {wallet.deposit_address}")
    
    # Send WebSocket notification
    channel_layer = get_channel_layer()
    group_name = f"deposit_address_{wallet.deposit_address}"
    
    message_data = {
        "type": "deposit_status_update",
        "data": {
            "address": wallet.deposit_address,
            "currency": "SOL",
            "network": "devnet",
            "status": "used",
            "amount": "1.0",
        }
    }
    
    try:
        print(f"Sending WebSocket message to group: {group_name}")
        print(f"Message data: {message_data}")
        
        async_to_sync(channel_layer.group_send)(group_name, message_data)
        
        print(f"Successfully sent WebSocket notification for address {wallet.deposit_address} with amount 1.0 SOL")
    except Exception as e:
        print(f"Failed to send WebSocket notification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_websocket()