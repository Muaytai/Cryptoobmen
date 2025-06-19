from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

from crypto.consumers import DepositConsumer

websocket_urlpatterns = [
    path('ws/deposit_status/<str:memo_id>/', DepositConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "websocket": URLRouter(websocket_urlpatterns)
}) 