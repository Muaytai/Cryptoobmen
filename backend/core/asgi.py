import os
from dotenv import load_dotenv

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path, re_path
from asgiref.sync import sync_to_async
from core.utils import lifespan

# Import WebSocket consumers directly
from crypto.consumers import DepositConsumer, DepositAddressConsumer

# Загружаем настройки из .env файла
load_dotenv()

# Установка переменных окружения Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Get the Django ASGI application
django_asgi_app = get_asgi_application()

# Define WebSocket URL patterns directly
websocket_urlpatterns = [
    re_path(r'ws/deposit_status/(?P<memo_id>[^/]+)/$', DepositConsumer.as_asgi()),
    re_path(r'ws/deposit_status/address/(?P<address>[^/]+)/$', DepositAddressConsumer.as_asgi()),
]

# Create the ASGI application
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
    "lifespan": lifespan,
})