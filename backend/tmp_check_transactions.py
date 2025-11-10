import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()
from crypto.blockchain.xrp import XRPService
svc = XRPService(network='testnet')
address = 'r3VjsrhhvisuBjbxrKbS1RCc2hTKbxD14w'
txs = svc.get_transactions(address)
print(address)
print(txs)
