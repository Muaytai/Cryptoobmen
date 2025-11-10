import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()
from crypto.models import UserDepositMemo
qs = UserDepositMemo.objects.filter(currency__symbol='XRP', status='waiting')
print(list(qs.values('memo','created_at')))
