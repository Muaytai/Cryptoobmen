from django.core.management.base import BaseCommand
from crypto.services import get_exchange_rates
from crypto.models import Cryptocurrency
from django.core.cache import cache
import requests

class Command(BaseCommand):
    help = "Тестирует загрузку цен криптовалют"

    def handle(self, *args, **options):
        self.stdout.write("=== Тестирование загрузки цен ===\n")
        
        # 1. Проверяем активные криптовалюты
        active_currencies = Cryptocurrency.objects.filter(
            is_active=True, 
            currency_type='crypto', 
            coingecko_id__isnull=False
        ).exclude(coingecko_id__exact='')
        
        self.stdout.write(f"Найдено активных криптовалют: {active_currencies.count()}")
        for crypto in active_currencies:
            self.stdout.write(f"  - {crypto.symbol} ({crypto.network}): coingecko_id={crypto.coingecko_id}")
        
        # 2. Очищаем кеш
        cache.clear()
        self.stdout.write("\nКеш очищен")
        
        # 3. Тестируем прямой запрос к API
        self.stdout.write("\n=== Прямой запрос к CoinGecko API ===")
        coingecko_ids = list(active_currencies.values_list('coingecko_id', flat=True))
        ids_string = ",".join(coingecko_ids)
        
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_string}&vs_currencies=usd"
        self.stdout.write(f"URL: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            self.stdout.write(f"Статус: {response.status_code}")
            self.stdout.write(f"Ответ: {response.text[:500]}")
            
            if response.status_code == 200:
                data = response.json()
                self.stdout.write("\nПолученные цены:")
                for crypto_id, prices in data.items():
                    usd_price = prices.get('usd', 'N/A')
                    self.stdout.write(f"  - {crypto_id}: ${usd_price}")
            else:
                self.stdout.write(self.style.ERROR(f"Ошибка API: {response.text}"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка запроса: {e}"))
        
        # 4. Тестируем нашу функцию
        self.stdout.write("\n=== Тестирование нашей функции get_exchange_rates ===")
        rates = get_exchange_rates()
        
        if rates:
            self.stdout.write("Цены получены успешно:")
            for crypto_id, data in rates.items():
                usd_price = data.get('usd', 'N/A')
                self.stdout.write(f"  - {crypto_id}: ${usd_price}")
        else:
            self.stdout.write(self.style.ERROR("Функция get_exchange_rates вернула None"))
        
        self.stdout.write("\n=== Тест завершен ===") 