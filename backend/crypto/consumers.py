import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import logging

logger = logging.getLogger(__name__)

class DepositConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.memo_id = self.scope['url_route']['kwargs']['memo_id']
        self.group_name = f'deposit_memo_{self.memo_id}'
        
        logger.info(f"DepositConsumer.connect called for memo_id: {self.memo_id}")

        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # Принимаем WebSocket
        await self.accept()
        
        logger.info(f"DepositConsumer.connect completed for memo_id: {self.memo_id}")

        # НЕ отправляем автоматически старые статусы при подключении,
        # чтобы избежать ложных уведомлений о "успешном пополнении"
        # Статус будет отправлен только при реальном изменении через deposit_status_update

    async def disconnect(self, close_code):
        logger.info(f"DepositConsumer.disconnect called for memo_id: {self.memo_id}")
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
        try:
            await self.send(text_data=json.dumps(event['data']))
            logger.info(f"Successfully sent WebSocket message to client for memo {self.memo_id}")
        except Exception as e:
            logger.error(f"Failed to send WebSocket message to client for memo {self.memo_id}: {e}")

    @database_sync_to_async
    def get_deposit_memo_status(self, memo_id):
        from crypto.models import UserDepositMemo
        try:
            memo = UserDepositMemo.objects.get(memo=memo_id)
            return memo.status
        except UserDepositMemo.DoesNotExist:
            return None 

class DepositAddressConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.address = self.scope['url_route']['kwargs']['address']
        self.group_name = f'deposit_address_{self.address}'
        
        logger.info(f"DepositAddressConsumer.connect called for address: {self.address}")
        logger.info(f"Group name: {self.group_name}")
        logger.info(f"Channel name: {self.channel_name}")

        # Присоединяемся к группе
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        logger.info(f"WebSocket connection established for address: {self.address}")

    async def disconnect(self, close_code):
        logger.info(f"DepositAddressConsumer.disconnect called for address: {self.address}")
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def deposit_status_update(self, event):
        # Отправляем событие клиенту
        logger.info(f"Received deposit_status_update event for address {self.address}: {event}")
        try:
            await self.send(text_data=json.dumps(event['data']))
            logger.info(f"Successfully sent WebSocket message to client for address {self.address}")
        except Exception as e:
            logger.error(f"Failed to send WebSocket message to client for address {self.address}: {e}")