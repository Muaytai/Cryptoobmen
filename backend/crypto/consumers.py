import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from crypto.models import UserDepositMemo

class DepositConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.memo_id = self.scope['url_route']['kwargs']['memo_id']
        self.group_name = f'deposit_memo_{self.memo_id}'

        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to group
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'deposit_status',
                'message': message
            }
        )

    # Receive message from group
    async def deposit_status(self, event):
        status = event['status']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'status': status
        }))

    @database_sync_to_async
    def get_deposit_memo_status(self, memo_id):
        try:
            memo = UserDepositMemo.objects.get(memo=memo_id)
            return memo.status
        except UserDepositMemo.DoesNotExist:
            return None 