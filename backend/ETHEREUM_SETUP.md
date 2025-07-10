# Настройка системы депозитов Ethereum (ERC20)

Этот документ описывает, как настроить и использовать систему отслеживания депозитов USDT в сети Ethereum (ERC20), аналогичную существующей системе для TRC20.

## Предварительные требования

1. **API ключи:**
   - `ETHERSCAN_API_KEY` - ключ от Etherscan API (https://etherscan.io/apis)
   - `ETHEREUM_RPC_URL` - URL для подключения к Ethereum RPC (например, Infura, Alchemy)

2. **Установленные зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

## Настройка переменных окружения

Добавьте следующие переменные в файл `.env.backend`:

```env
# Ethereum настройки
ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/YOUR_PROJECT_ID
ETHERSCAN_API_KEY=YOUR_ETHERSCAN_API_KEY
ETHEREUM_NETWORK=mainnet  # или sepolia, goerli для тестовых сетей

# Существующие настройки
TRONGRID_API_KEY=YOUR_TRONGRID_API_KEY
TRON_NETWORK=nile
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
```

## Получение API ключей

### Etherscan API Key
1. Зарегистрируйтесь на https://etherscan.io/
2. Перейдите в раздел API-KEYs
3. Создайте новый API ключ
4. Скопируйте ключ в переменную `ETHERSCAN_API_KEY`

### Ethereum RPC URL
1. **Infura** (https://infura.io/):
   - Зарегистрируйтесь и создайте проект
   - Скопируйте URL: `https://mainnet.infura.io/v3/YOUR_PROJECT_ID`

2. **Alchemy** (https://alchemy.com/):
   - Зарегистрируйтесь и создайте приложение
   - Скопируйте HTTP URL

3. **Локальный узел** (если у вас есть):
   - `http://localhost:8545`

## Инициализация базы данных

1. **Примените миграции:**
   ```bash
   python manage.py migrate
   ```

2. **Создайте тестовые данные:**
   ```bash
   python manage.py seed_crypto_data
   ```

3. **Создайте системные кошельки для Ethereum:**
   ```bash
   python manage.py shell
   ```
   
   ```python
   from crypto.models import Cryptocurrency, SystemWalletAddress
   
   # Создаем валюту USDT ERC20 если её нет
   usdt_erc20, created = Cryptocurrency.objects.get_or_create(
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
   system_wallet, created = SystemWalletAddress.objects.get_or_create(
       currency=usdt_erc20,
       network='ERC20',
       defaults={
           'address': '0xYOUR_SYSTEM_WALLET_ADDRESS',
       }
   )
   
   print(f"Системный кошелек создан: {system_wallet.address}")
   ```

## Запуск системы

### 1. Непрерывное отслеживание
```bash
python manage.py listen_ethereum_deposits
```

### 2. Умный старт (обработка пропущенных блоков)
```bash
python manage.py listen_ethereum_deposits --smart-start
```

### 3. Однократная проверка
```bash
python manage.py listen_ethereum_deposits --once
```

### 4. Сканирование через Celery task
```bash
python manage.py scan_ethereum_deposits
```

## Особенности Ethereum (ERC20)

### Отличия от TRC20

1. **Memo система:**
   - Ethereum не имеет встроенной системы memo как TRC20
   - Memo извлекается из input data транзакции
   - Требуется более сложная логика для извлечения memo

2. **Комиссии:**
   - Комиссии за транзакции в ETH (gas fees)
   - Более высокие комиссии по сравнению с TRC20

3. **Подтверждения:**
   - Больше времени на подтверждение транзакций
   - Рекомендуется ждать несколько блоков

### Настройка memo для Ethereum

Поскольку Ethereum не поддерживает memo напрямую, используется один из подходов:

1. **Input data в транзакции:**
   - Memo передается в поле input данных транзакции
   - Система пытается декодировать memo из input data

2. **Специальные контракты:**
   - Можно использовать специальные смарт-контракты для передачи memo
   - Более сложная реализация, но более надежная

## Мониторинг и логирование

### Логи
Система ведет подробные логи в Django логах:
```python
import logging
logger = logging.getLogger(__name__)
```

### Проверка статуса
```bash
# Проверка активных кошельков
python manage.py shell
```
```python
from crypto.models import SystemWalletAddress
wallets = SystemWalletAddress.objects.filter(network='ERC20')
for wallet in wallets:
    print(f"{wallet.currency.symbol}: {wallet.address}")
```

### Проверка транзакций
```python
from transactions.models import Transaction
from crypto.models import Cryptocurrency

usdt_erc20 = Cryptocurrency.objects.get(symbol='USDT', network='ERC20')
transactions = Transaction.objects.filter(crypto=usdt_erc20).order_by('-timestamp')[:10]
for tx in transactions:
    print(f"{tx.tx_hash}: {tx.amount} {tx.crypto.symbol}")
```

## Устранение неполадок

### Ошибки подключения
1. **Проверьте RPC URL:**
   ```bash
   curl -X POST -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' YOUR_RPC_URL
   ```

2. **Проверьте Etherscan API:**
   ```bash
   curl "https://api.etherscan.io/api?module=account&action=balance&address=0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6&tag=latest&apikey=YOUR_API_KEY"
   ```

### Ошибки обработки транзакций
1. **Проверьте логи Django:**
   ```bash
   tail -f logs/django.log
   ```

2. **Проверьте состояние мемо-кодов:**
   ```python
   from crypto.models import UserDepositMemo
   memos = UserDepositMemo.objects.filter(network='ERC20', status='waiting')
   for memo in memos:
       print(f"Memo: {memo.memo}, User: {memo.user.email}, Expires: {memo.expires_at}")
   ```

## Безопасность

1. **Хранение приватных ключей:**
   - Никогда не храните приватные ключи в открытом виде
   - Используйте шифрование для системных кошельков

2. **API ключи:**
   - Храните API ключи в переменных окружения
   - Не коммитьте их в репозиторий

3. **Валидация адресов:**
   - Всегда проверяйте checksum адресов Ethereum
   - Используйте Web3.py для валидации

## Производительность

1. **Rate limiting:**
   - Etherscan имеет лимиты на API запросы
   - Используйте кэширование где возможно

2. **Оптимизация запросов:**
   - Группируйте запросы к API
   - Используйте batch запросы

3. **Мониторинг:**
   - Следите за временем ответа API
   - Настройте алерты при превышении лимитов 