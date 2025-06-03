import requests
from django.conf import settings
from .models import Cryptocurrency

# Можно вынести в настройки, если URL или параметры будут меняться
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"

def get_exchange_rates():
    """
    Получает актуальные курсы для активных криптовалют к USD с CoinGecko.
    Возвращает словарь вида: {'coingecko_id': {'usd': rate}}
    Например: {'bitcoin': {'usd': 60000.0}, ...}
    Или None в случае ошибки.
    """
    active_currencies = Cryptocurrency.objects.filter(
        is_active=True, 
        currency_type='crypto', 
        coingecko_id__isnull=False
    ).exclude(coingecko_id__exact='')

    if not active_currencies:
        print("[DEBUG] No active crypto currencies with coingecko_id found in DB.")
        return {} 

    coingecko_ids = [currency.coingecko_id for currency in active_currencies]
    ids_string = ",".join(coingecko_ids)
    
    print(f"[DEBUG] Requesting Coingecko for IDs: {ids_string}")
    
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_string}&vs_currencies=usd"
    print(f"[DEBUG] Coingecko URL: {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        rates = response.json()
        print(f"[DEBUG] Received from Coingecko: {rates}")
        return rates
    except requests.exceptions.HTTPError as http_err:
        print(f"[ERROR] HTTP error occurred: {http_err} - Response: {response.text}")
        return None
    except requests.exceptions.ConnectionError as conn_err:
        print(f"[ERROR] Connection error occurred: {conn_err}")
        return None
    except requests.exceptions.Timeout as timeout_err:
        print(f"[ERROR] Timeout error occurred: {timeout_err}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"[ERROR] An error occurred: {req_err}")
        return None
    except ValueError as json_err: 
        print(f"[ERROR] JSON decode error: {json_err} - Response: {response.text}")
        return None

# Пример использования (можно добавить в shell или тесты):
# if __name__ == '__main__':
#     # Для запуска этого примера напрямую, нужно настроить Django окружение
#     # django.setup() # Это если запускать как отдельный скрипт
#     rates = get_exchange_rates()
#     if rates:
#         for crypto_id, data in rates.items():
#             print(f"1 {crypto_id.upper()} = {data.get('usd')} USD")
#     else:
#         print("Could not fetch exchange rates.") 