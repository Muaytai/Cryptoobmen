import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from crypto.models import Cryptocurrency, CryptoPrice # Ensure these imports are correct
from decimal import Decimal
import time

# ID криптовалют в CoinGecko (примеры, вам нужно будет найти актуальные ID для ваших криптовалют)
# Вы можете получить список всех монет здесь: https://api.coingecko.com/api/v3/coins/list
COINGECKO_IDS = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'USDT': 'tether',
    # Добавьте другие ваши криптовалюты и их ID в CoinGecko
    # Например: 'SOL': 'solana', 'BNB': 'binancecoin'
}

COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"

class Command(BaseCommand):
    help = 'Обновляет цены на криптовалюты с CoinGecko API'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Начало обновления цен на криптовалюты..."))

        active_cryptos = Cryptocurrency.objects.filter(is_active=True)
        if not active_cryptos.exists(): # Use .exists() for efficiency
            self.stdout.write(self.style.WARNING("Нет активных криптовалют для обновления цен."))
            return

        symbols_to_fetch_cg_ids = []
        crypto_map_by_cg_id = {}

        for crypto in active_cryptos:
            cg_id = COINGECKO_IDS.get(crypto.symbol.upper()) # Normalize symbol to upper for matching
            if cg_id:
                symbols_to_fetch_cg_ids.append(cg_id)
                crypto_map_by_cg_id[cg_id] = crypto # Map CoinGecko ID back to Cryptocurrency object
            else:
                self.stdout.write(self.style.WARNING(f"CoinGecko ID не найден для символа: {crypto.symbol}"))

        if not symbols_to_fetch_cg_ids:
            self.stdout.write(self.style.WARNING("Нет активных криптовалют с известными CoinGecko ID для запроса."))
            return

        coingecko_ids_string = ",".join(symbols_to_fetch_cg_ids)

        params = {
            'ids': coingecko_ids_string,
            'vs_currencies': 'usd',
        }

        try:
            self.stdout.write(f"Запрос к CoinGecko API для ID: {coingecko_ids_string}")
            response = requests.get(COINGECKO_API_URL, params=params, timeout=20) # Increased timeout
            response.raise_for_status()
            prices_data = response.json()
            
            self.stdout.write(f"Получены данные от CoinGecko: {prices_data}")

            prices_created_count = 0
            for cg_id, price_info in prices_data.items():
                crypto_obj = crypto_map_by_cg_id.get(cg_id)
                if crypto_obj:
                    price_usd_str = price_info.get('usd')
                    if price_usd_str is not None:
                        try:
                            price_usd = Decimal(str(price_usd_str))
                            CryptoPrice.objects.create(
                                crypto=crypto_obj,
                                price_usd=price_usd
                            )
                            prices_created_count += 1
                            self.stdout.write(self.style.SUCCESS(f"Цена для {crypto_obj.symbol} обновлена: ${price_usd}"))
                        except Exception as e:
                            self.stderr.write(self.style.ERROR(f"Ошибка преобразования или сохранения цены для {crypto_obj.symbol} ({cg_id}): {price_usd_str}. Ошибка: {e}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"Цена в USD не найдена для {cg_id} в ответе CoinGecko."))
                else:
                    # Should not happen if crypto_map_by_cg_id is built correctly
                    self.stdout.write(self.style.WARNING(f"Не удалось найти объект Cryptocurrency для CoinGecko ID: {cg_id}"))
            
            if prices_created_count > 0:
                self.stdout.write(self.style.SUCCESS(f"Успешно создано/обновлено {prices_created_count} записей о ценах."))
            else:
                self.stdout.write(self.style.WARNING("Не было создано ни одной новой записи о ценах. Возможно, данные уже актуальны или возникли проблемы с сопоставлением."))

        except requests.exceptions.Timeout:
            self.stderr.write(self.style.ERROR(f"Ошибка тайм-аута при запросе к CoinGecko API."))
        except requests.exceptions.HTTPError as e:
            self.stderr.write(self.style.ERROR(f"HTTP ошибка при запросе к CoinGecko API: {e} (Статус: {e.response.status_code}, Ответ: {e.response.text[:200]}...)"))
        except requests.exceptions.RequestException as e:
            self.stderr.write(self.style.ERROR(f"Ошибка при запросе к CoinGecko API: {e}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Непредвиденная ошибка при обновлении цен: {e}"))

        self.stdout.write(self.style.NOTICE("Обновление цен завершено."))
