from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, CryptoPrice
from crypto.services import get_exchange_rates
from decimal import Decimal
from datetime import datetime, timezone
import requests
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Создает актуальные цены для криптовалют через API CoinGecko'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force-update',
            action='store_true',
            help='Принудительно обновить все цены, даже если они уже существуют',
        )
        parser.add_argument(
            '--test-mode',
            action='store_true',
            help='Использовать тестовые цены вместо API (для отладки)',
        )

    def handle(self, *args, **options):
        force_update = options['force_update']
        test_mode = options['test_mode']
        
        self.stdout.write("=== СОЗДАНИЕ АКТУАЛЬНЫХ ЦЕН КРИПТОВАЛЮТ ===")
        
        # Получаем все активные криптовалюты
        cryptocurrencies = Cryptocurrency.objects.filter(is_active=True, currency_type='crypto')
        
        if not cryptocurrencies.exists():
            self.stdout.write(self.style.WARNING("Нет активных криптовалют в базе данных"))
            self.stdout.write("Сначала запустите: python manage.py seed_crypto_data")
            return
        
        self.stdout.write(f"Найдено {cryptocurrencies.count()} активных криптовалют")
        
        if test_mode:
            self.stdout.write(self.style.WARNING("Режим тестирования: используются тестовые цены"))
            self._create_test_prices(cryptocurrencies, force_update)
        else:
            self.stdout.write("Получение актуальных цен через API CoinGecko...")
            self._create_api_prices(cryptocurrencies, force_update)

    def _create_api_prices(self, cryptocurrencies, force_update):
        """Создает цены через API CoinGecko"""
        
        # Получаем курсы через наш сервис
        try:
            rates = get_exchange_rates()
            if not rates:
                self.stdout.write(self.style.ERROR("✗ Не удалось получить курсы через API"))
                self.stdout.write("Попробуйте использовать --test-mode для создания тестовых цен")
                return
            
            self.stdout.write(self.style.SUCCESS(f"✓ Получено {len(rates)} курсов через API"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Ошибка API: {e}"))
            self.stdout.write("Попробуйте использовать --test-mode для создания тестовых цен")
            return
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for crypto in cryptocurrencies:
            self.stdout.write(f"\n--- {crypto.symbol} ({crypto.network}) ---")
            
            # Ищем цену по coingecko_id
            if not crypto.coingecko_id:
                self.stdout.write(self.style.WARNING(f"! Нет coingecko_id для {crypto.symbol}"))
                skipped_count += 1
                continue
            
            price_data = rates.get(crypto.coingecko_id)
            if not price_data or 'usd' not in price_data:
                self.stdout.write(self.style.WARNING(f"! Нет данных о цене для {crypto.symbol} ({crypto.coingecko_id})"))
                skipped_count += 1
                continue
            
            price_usd = Decimal(str(price_data['usd']))
            self.stdout.write(f"  Цена: ${price_usd}")
            
            # Проверяем, есть ли уже цены для этой валюты
            existing_prices = CryptoPrice.objects.filter(crypto=crypto)
            
            if existing_prices.exists() and not force_update:
                # Проверяем, не слишком ли старая цена (больше 1 часа)
                latest_price = existing_prices.order_by('-timestamp').first()
                time_diff = datetime.now(timezone.utc) - latest_price.timestamp
                
                if time_diff.total_seconds() < 3600:  # 1 час
                    self.stdout.write(self.style.SUCCESS(f"✓ Цена актуальна (обновлена {time_diff.total_seconds()/60:.1f} мин назад)"))
                    skipped_count += 1
                    continue
                else:
                    # Обновляем старую цену
                    latest_price.price_usd = price_usd
                    latest_price.timestamp = datetime.now(timezone.utc)
                    latest_price.save()
                    self.stdout.write(self.style.SUCCESS(f"✓ Обновлена цена: ${price_usd}"))
                    updated_count += 1
            else:
                # Создаем новую запись цены
                CryptoPrice.objects.create(
                    crypto=crypto,
                    price_usd=price_usd,
                    price_btc=Decimal('0.0'),
                    price_eth=Decimal('0.0'),
                    market_cap=Decimal('0.0'),
                    volume_24h=Decimal('0.0'),
                )
                self.stdout.write(self.style.SUCCESS(f"✓ Создана цена: ${price_usd}"))
                created_count += 1
        
        self._print_summary(created_count, updated_count, skipped_count)

    def _create_test_prices(self, cryptocurrencies, force_update):
        """Создает тестовые цены (для отладки)"""
        
        # Тестовые цены (примерные)
        test_prices = {
            'USDT': Decimal('1.00'),
            'BTC': Decimal('45000.00'),
            'ETH': Decimal('2800.00'),
            'SOL': Decimal('95.00'),
            'TRX': Decimal('0.08'),
            'BNB': Decimal('320.00'),
            'XRP': Decimal('0.55'),
        }
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for crypto in cryptocurrencies:
            self.stdout.write(f"\n--- {crypto.symbol} ({crypto.network}) ---")
            
            # Определяем цену для валюты
            if crypto.symbol in test_prices:
                price_usd = test_prices[crypto.symbol]
            else:
                # Для неизвестных валют используем случайную цену
                import random
                price_usd = Decimal(str(random.uniform(0.01, 100.0)))
            
            # Проверяем, есть ли уже цены для этой валюты
            existing_prices = CryptoPrice.objects.filter(crypto=crypto)
            
            if existing_prices.exists() and not force_update:
                self.stdout.write(self.style.SUCCESS(f"✓ Цена уже существует: ${existing_prices.first().price_usd}"))
                skipped_count += 1
            else:
                if existing_prices.exists():
                    # Обновляем последнюю цену
                    latest_price = existing_prices.order_by('-timestamp').first()
                    latest_price.price_usd = price_usd
                    latest_price.timestamp = datetime.now(timezone.utc)
                    latest_price.save()
                    self.stdout.write(self.style.SUCCESS(f"✓ Обновлена цена: ${price_usd}"))
                    updated_count += 1
                else:
                    # Создаем новую запись цены
                    CryptoPrice.objects.create(
                        crypto=crypto,
                        price_usd=price_usd,
                        price_btc=Decimal('0.0'),
                        price_eth=Decimal('0.0'),
                        market_cap=Decimal('0.0'),
                        volume_24h=Decimal('0.0'),
                    )
                    self.stdout.write(self.style.SUCCESS(f"✓ Создана цена: ${price_usd}"))
                    created_count += 1
        
        self._print_summary(created_count, updated_count, skipped_count)

    def _print_summary(self, created_count, updated_count, skipped_count):
        """Выводит итоговую статистику"""
        self.stdout.write(f"\n=== РЕЗУЛЬТАТ ===")
        self.stdout.write(f"Создано новых цен: {created_count}")
        self.stdout.write(f"Обновлено цен: {updated_count}")
        self.stdout.write(f"Пропущено (уже актуальны): {skipped_count}")
        self.stdout.write(self.style.SUCCESS("Цены созданы/обновлены успешно!"))
        
        # Проверяем результат
        total_prices = CryptoPrice.objects.count()
        self.stdout.write(f"Всего цен в базе: {total_prices}")
        
        if total_prices > 0:
            self.stdout.write("\nПоследние цены:")
            recent_prices = CryptoPrice.objects.all().order_by('-timestamp')[:5]
            for price in recent_prices:
                self.stdout.write(f"  {price.crypto.symbol}: ${price.price_usd}")
        
        self.stdout.write(f"\nИспользование:")
        self.stdout.write(f"  python manage.py create_crypto_prices                    # Обычный запуск")
        self.stdout.write(f"  python manage.py create_crypto_prices --force-update    # Принудительное обновление")
        self.stdout.write(f"  python manage.py create_crypto_prices --test-mode       # Тестовые цены")
