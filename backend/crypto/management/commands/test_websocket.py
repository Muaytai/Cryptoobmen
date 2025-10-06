from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test WebSocket functionality by sending a test message'

    def add_arguments(self, parser):
        parser.add_argument('--address', type=str, help='Test address to send message to')
        parser.add_argument('--memo', type=str, help='Test memo to send message to')

    def handle(self, *args, **options):
        self.stdout.write("=== Testing WebSocket functionality ===\n")
        
        channel_layer = get_channel_layer()
        if not channel_layer:
            self.stdout.write(self.style.ERROR("✗ Channel layer not configured"))
            return
            
        self.stdout.write(self.style.SUCCESS("✓ Channel layer available"))
        
        if options['address']:
            group_name = f"deposit_address_{options['address']}"
            message_data = {
                "type": "deposit_status_update",
                "data": {
                    "address": options['address'],
                    "currency": "SOL",
                    "network": "solana",
                    "status": "used",
                    "amount": "1.0",
                }
            }
            self.stdout.write(f"Sending test message to group: {group_name}")
            try:
                async_to_sync(channel_layer.group_send)(group_name, message_data)
                self.stdout.write(self.style.SUCCESS("✓ Test message sent successfully"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Failed to send test message: {e}"))
                
        elif options['memo']:
            group_name = f"deposit_memo_{options['memo']}"
            message_data = {
                "type": "deposit_status_update",
                "data": {
                    "memo": options['memo'],
                    "status": "used",
                    "message": "Test deposit completed"
                }
            }
            self.stdout.write(f"Sending test message to group: {group_name}")
            try:
                async_to_sync(channel_layer.group_send)(group_name, message_data)
                self.stdout.write(self.style.SUCCESS("✓ Test message sent successfully"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Failed to send test message: {e}"))
        else:
            self.stdout.write("Please provide either --address or --memo argument")