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

        # НЕ отправляем автоматически старые статусы при подключении,
        # чтобы избежать ложных уведомлений о "успешном пополнении"
        # Статус будет отправлен только при реальном изменении через deposit_status_update

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

class DepositAddressConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        import logging
        logger = logging.getLogger(__name__)
        
        self.address = self.scope['url_route']['kwargs']['address']
        # Приводим адрес к нижнему регистру для единообразия
        address_lower = self.address.lower()
        self.group_name = f'deposit_address_{address_lower}'
        
        logger.info(f"DepositAddressConsumer: Attempting to connect for address {self.address} (normalized: {address_lower}), group: {self.group_name}")

        try:
            # Присоединяемся к группе
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
            logger.info(f"DepositAddressConsumer: Successfully connected for address {self.address}")
        except Exception as e:
            logger.error(f"DepositAddressConsumer: Error connecting for address {self.address}: {e}", exc_info=True)
            raise

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def deposit_status_update(self, event):
        # Отправляем событие клиенту
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"DepositAddressConsumer: Received deposit_status_update for address {self.address}, group {self.group_name}, data: {event['data']}")
        await self.send(text_data=json.dumps(event['data']))
        logger.info(f"DepositAddressConsumer: Message sent to WebSocket client for {self.address}") 