import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()
from crypto.models import SystemWalletAddress, Cryptocurrency
cur = Cryptocurrency.objects.get(symbol='XRP', network='XRP')
print(list(SystemWalletAddress.objects.filter(currency=cur).values('address','network')))
