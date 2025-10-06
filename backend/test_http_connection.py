import requests

def test_http_connection():
    # Test different URLs
    urls = [
        "http://localhost:8000/ws/deposit_status/address/test/",
        "http://127.0.0.1:8000/ws/deposit_status/address/test/",
    ]
    
    for url in urls:
        print(f"Testing HTTP connection to {url}")
        try:
            response = requests.head(url, timeout=5)
            print(f"Status code: {response.status_code}")
            print(f"Headers: {response.headers}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to connect: {e}")
        print()

if __name__ == "__main__":
    test_http_connection()