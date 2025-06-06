import requests
from django.conf import settings
import logging

# Настройка логгера
logger = logging.getLogger(__name__)

# Можно вынести в настройки, если URL или параметры будут меняться
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"

def get_exchange_rates(vs_currencies=None):
    """
    Получает актуальные курсы для активных криптовалют с CoinGecko.
    
    :param vs_currencies: Список строковых идентификаторов целевых валют (например, ['usd', 'eur', 'btc']).
                          Если None, по умолчанию используется ['usd'].
    :return: Словарь вида: {'coingecko_id': {'usd': rate, 'eur': rate, ...}}
             Например: {'bitcoin': {'usd': 60000.0, 'eur': 50000.0}, ...}
             Или None в случае ошибки.
    """
    from .models import Cryptocurrency  # Импорт перенесен сюда для избежания цикла
    
    if vs_currencies is None:
        vs_currencies = ['usd']
        
    active_currencies = Cryptocurrency.objects.filter(
        is_active=True, 
        currency_type='crypto', 
        coingecko_id__isnull=False
    ).exclude(coingecko_id__exact='')

    if not active_currencies.exists():
        logger.warning("No active cryptocurrencies with coingecko_id found. Nothing to fetch.")
        return {} 

    coingecko_ids = list(active_currencies.values_list('coingecko_id', flat=True))
    ids_string = ",".join(coingecko_ids)
    vs_currencies_string = ",".join(vs_currencies)
    
    params = {
        'ids': ids_string,
        'vs_currencies': vs_currencies_string
    }
    
    logger.debug(f"Requesting Coingecko for IDs: {ids_string} against VS Currencies: {vs_currencies_string}")

    try:
        response = requests.get(COINGECKO_API_URL, params=params, timeout=10)
        response.raise_for_status()
        rates = response.json()
        logger.debug(f"Received from Coingecko: {rates}")
        return rates
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err} - Status: {response.status_code} - Response: {response.text}")
        return None
    except requests.exceptions.RequestException as req_err:
        logger.error(f"An error occurred during Coingecko request: {req_err}")
        return None
    except ValueError as json_err: 
        logger.error(f"JSON decode error: {json_err} - Response: {response.text}")
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