import asyncio
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class Command(BaseCommand):
    help = 'Test WebSocket endpoints'

    def handle(self, *args, **options):
        self.stdout.write('Testing WebSocket endpoints...')
        
        # Test sending a message to a WebSocket group
        channel_layer = get_channel_layer()
        group_name = "deposit_address_5s9HUwUzaDWtJvGCuSns31QGgr8PLqdocuuGk4bkaBZK"
        
        message_data = {
            "type": "deposit_status_update",
            "data": {
                "address": "5s9HUwUzaDWtJvGCuSns31QGgr8PLqdocuuGk4bkaBZK",
                "currency": "SOL",
                "network": "devnet",
                "status": "used",
                "amount": "1.0",
            }
        }
        
        try:
            self.stdout.write(f'Sending WebSocket message to group: {group_name}')
            self.stdout.write(f'Message data: {message_data}')
            
            async_to_sync(channel_layer.group_send)(group_name, message_data)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully sent WebSocket notification for address 5s9HUwUzaDWtJvGCuSns31QGgr8PLqdocuuGk4bkaBZK with amount 1.0 SOL'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Failed to send WebSocket notification: {e}'
                )
            )
            import traceback
            traceback.print_exc()