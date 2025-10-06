import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def test_routing():
    from django.urls import resolve
    from channels.routing import get_default_application
    import asyncio
    
    # Test routing resolution
    try:
        # Test memo path
        memo_path = "/ws/deposit_status/test_memo/"
        match = resolve(memo_path)
        print(f"Memo path '{memo_path}' resolves to: {match}")
    except Exception as e:
        print(f"Failed to resolve memo path: {e}")
    
    try:
        # Test address path
        address_path = "/ws/deposit_status/address/test_address/"
        match = resolve(address_path)
        print(f"Address path '{address_path}' resolves to: {match}")
    except Exception as e:
        print(f"Failed to resolve address path: {e}")

if __name__ == "__main__":
    test_routing()