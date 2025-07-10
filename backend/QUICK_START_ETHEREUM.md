# Быстрый старт: Ethereum депозиты

## 1. Настройка переменных окружения

Создайте файл `.env.backend` в корне проекта:

```env
# Ethereum
ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/YOUR_PROJECT_ID
ETHERSCAN_API_KEY=YOUR_ETHERSCAN_API_KEY
ETHEREUM_NETWORK=mainnet

# База данных
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
```

## 2. Получение API ключей

### Infura (RPC)
1. Зарегистрируйтесь на https://infura.io/
2. Создайте проект
3. Скопируйте URL: `https://mainnet.infura.io/v3/YOUR_PROJECT_ID`

### Etherscan (API)
1. Зарегистрируйтесь на https://etherscan.io/
2. Создайте API ключ
3. Скопируйте ключ

## 3. Тестирование подключения

```bash
python test_ethereum_connection.py
```

## 4. Инициализация базы данных

```bash
python manage.py migrate
python manage.py seed_crypto_data
```

## 5. Создание системного кошелька

```bash
python manage.py shell
```

```python
from crypto.models import Cryptocurrency, SystemWalletAddress

# Создаем валюту USDT ERC20
usdt_erc20, _ = Cryptocurrency.objects.get_or_create(
    symbol='USDT',
    network='ERC20',
    defaults={
        'name': 'Tether USD',
        'coingecko_id': 'tether',
        'contract_address': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
        'decimals': 6,
        'is_active': True,
    }
)

# Создаем системный кошелек (замените на реальный адрес)
system_wallet, _ = SystemWalletAddress.objects.get_or_create(
    currency=usdt_erc20,
    network='ERC20',
    defaults={
        'address': '0xYOUR_SYSTEM_WALLET_ADDRESS',
    }
)

print(f"Системный кошелек: {system_wallet.address}")
```

## 6. Запуск системы

### Непрерывное отслеживание
```bash
python manage.py listen_ethereum_deposits
```

### Однократная проверка
```bash
python manage.py listen_ethereum_deposits --once
```

### Умный старт (обработка пропущенных блоков)
```bash
python manage.py listen_ethereum_deposits --smart-start
```

## 7. Проверка работы

```bash
python manage.py shell
```

```python
from crypto.models import SystemWalletAddress
from transactions.models import Transaction

# Проверяем активные кошельки
wallets = SystemWalletAddress.objects.filter(network='ERC20')
for wallet in wallets:
    print(f"{wallet.currency.symbol}: {wallet.address}")

# Проверяем транзакции
transactions = Transaction.objects.filter(crypto__network='ERC20').order_by('-timestamp')[:5]
for tx in transactions:
    print(f"{tx.tx_hash}: {tx.amount} {tx.crypto.symbol}")
```

## Команды для отладки

```bash
# Тест подключения
python test_ethereum_connection.py

# Сканирование через Celery
python manage.py scan_ethereum_deposits

# Проверка логов
tail -f logs/django.log
```

## Стоп-словарь

- **RPC URL** - адрес для подключения к Ethereum сети
- **Etherscan API** - сервис для получения данных о транзакциях
- **ERC20** - стандарт токенов на Ethereum
- **Memo** - идентификатор для связи транзакции с пользователем
- **Gas fees** - комиссии за транзакции в Ethereum 