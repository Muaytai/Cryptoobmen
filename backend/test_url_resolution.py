import os
import sys
import django
from django.conf import settings
from django.urls import resolve, reverse

# Add the project directory to Python path
sys.path.append('d:\\PythonProjects\\Cryptoobmen\\backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def test_url_resolution():
    try:
        # Test if the URL patterns are correctly defined
        from django.urls import get_resolver
        resolver = get_resolver()
        
        # Print all URL patterns
        print("URL patterns:")
        for pattern in resolver.url_patterns:
            print(f"  {pattern.pattern}")
            
    except Exception as e:
        print(f"Failed to resolve URL patterns: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_url_resolution()