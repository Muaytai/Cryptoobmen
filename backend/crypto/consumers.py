import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class DepositConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.memo_id = self.scope['url_route']['kwargs']['memo_id']
        self.group_name = f'deposit_memo_{self.memo_id}'

        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # Принимаем WebSocket
        await self.accept()

        # Сразу отправляем текущее состояние депозита, чтобы клиент не зависал в ожидании,
        # если статус уже изменился до подключения
        current_status = await self.get_deposit_memo_status(self.memo_id)
        if current_status:
            await self.send(text_data=json.dumps({
                'memo': self.memo_id,
                'status': current_status,
            }))

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    # async def receive(self, text_data):
    #     pass

    # Receive message from group
    async def deposit_status_update(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event['data']))

    @database_sync_to_async
    def get_deposit_memo_status(self, memo_id):
        from crypto.models import UserDepositMemo
        try:
            memo = UserDepositMemo.objects.get(memo=memo_id)
            return memo.status
        except UserDepositMemo.DoesNotExist:
            return None 