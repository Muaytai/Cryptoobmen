from django.core.management.base import BaseCommand
from crypto.models import UserWallet, Cryptocurrency
from django.contrib.auth import get_user_model
import asyncio
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class Command(BaseCommand):
    help = 'Test Solana WebSocket notification'

    def add_arguments(self, parser):
        parser.add_argument('--address', type=str, help='Deposit address to test')
        parser.add_argument('--amount', type=str, default='1.0', help='Amount to simulate')

    def handle(self, *args, **options):
        address = options['address']
        amount = options['amount']
        
        if not address:
            # Create a test wallet if no address provided
            User = get_user_model()
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR('No users found. Please create a user first.'))
                return
                
            crypto = Cryptocurrency.objects.get(symbol='SOL')
            wallet, created = UserWallet.objects.get_or_create(
                user=user, 
                currency=crypto, 
                defaults={
                    'balance': 0, 
                    'is_system_wallet': False, 
                    'is_active': True
                }
            )
            address = wallet.deposit_address
            if not address:
                self.stdout.write(self.style.ERROR('No deposit address found for wallet.'))
                return
                
            self.stdout.write(f'Using wallet address: {address}')
        
        # Send WebSocket notification
        channel_layer = get_channel_layer()
        group_name = f"deposit_address_{address}"
        
        message_data = {
            "type": "deposit_status_update",
            "data": {
                "address": address,
                "currency": "SOL",
                "network": "devnet",
                "status": "used",
                "amount": amount,
            }
        }
        
        try:
            self.stdout.write(f'Sending WebSocket message to group: {group_name}')
            self.stdout.write(f'Message data: {message_data}')
            
            async_to_sync(channel_layer.group_send)(group_name, message_data)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully sent WebSocket notification for address {address} with amount {amount} SOL'
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to send WebSocket notification: {e}'))