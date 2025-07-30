# Интеграция Ethereum и ERC-20 токенов

## Обзор

Данная документация описывает интеграцию поддержки Ethereum (ETH) и ERC-20 токенов в криптовалютную платформу Cryptoobmen.

## Архитектура

### Компоненты интеграции

1. **EthereumService** (`crypto/blockchain/ethereum.py`)
   - Основной сервис для взаимодействия с Ethereum блокчейном
   - Поддерживает операции с ETH и ERC-20 токенами
   - Использует Web3.py для подключения к Ethereum сети

2. **Factory Pattern** (`crypto/blockchain/factory.py`)
   - Обновлен для поддержки Ethereum сервиса
   - Автоматически выбирает правильный сервис по типу сети

3. **Celery Tasks** (`crypto/tasks.py`)
   - Обновлены для сканирования Ethereum транзакций
   - Поддержка обработки депозитов и выводов

## Настройки

### Переменные окружения (.env.backend)

```bash
# Ethereum настройки
ETHEREUM_NETWORK=goerli                    # mainnet, goerli, sepolia
ETHEREUM_RPC_URL=https://goerli.infura.io/v3/YOUR_PROJECT_ID
ETHEREUM_BACKUP_RPC_URL=https://eth-goerli.alchemyapi.io/v2/YOUR_API_KEY
INFURA_PROJECT_ID=YOUR_INFURA_PROJECT_ID
ALCHEMY_API_KEY=YOUR_ALCHEMY_API_KEY

# Ethereum контракты (Goerli testnet адреса)
USDT_ERC20_CONTRACT_ADDRESS=0x509Ee0d083DdF8AC028f2a56731412edD63223B9
USDC_ERC20_CONTRACT_ADDRESS=0x07865c6E87B9F70255377e024ace6630C1Eaa37F
DAI_ERC20_CONTRACT_ADDRESS=0x11fE4B6AE13d2a6055C8D9cF65c55bac32B5d844

# Gas настройки
ETHEREUM_GAS_PRICE_MULTIPLIER=1.2
ETHEREUM_MAX_GAS_PRICE=50
ETHEREUM_GAS_LIMIT_ETH=21000
ETHEREUM_GAS_LIMIT_ERC20=65000

# Системный кошелек (ТОЛЬКО ДЛЯ РАЗРАБОТКИ!)
ETHEREUM_PLATFORM_PRIVATE_KEY=YOUR_PRIVATE_KEY_HERE
```

### Django настройки (core/settings.py)

Все необходимые настройки автоматически загружаются из переменных окружения.

## Зависимости

### Python пакеты (requirements.txt)

```
web3==7.12.0
eth-account==0.13.7
eth-utils==5.3.0
eth-typing==5.2.1
hexbytes==1.3.1
```

## Использование

### Создание нового адреса

```python
from crypto.blockchain.ethereum import EthereumService

service = EthereumService()
address, private_key = service.create_new_address()
```

### Получение баланса

```python
# ETH баланс
eth_balance = service.get_balance(address)

# ERC-20 токен баланс
token_balance = service.get_balance(address, contract_address='0x...')
```

### Отправка транзакции

```python
# Отправка ETH
tx_hash = service.send_transaction(
    private_key='0x...',
    to_address='0x...',
    amount=Decimal('0.1')
)

# Отправка ERC-20 токена
tx_hash = service.send_transaction(
    private_key='0x...',
    to_address='0x...',
    amount=Decimal('100'),
    contract_address='0x...'
)
```

### Сканирование транзакций

```python
# ETH транзакции
transactions = service.get_transactions(address, min_timestamp=0)

# ERC-20 транзакции
transactions = service.get_transactions(
    address, 
    min_timestamp=0, 
    contract_address='0x...'
)
```

## Тестирование

### Команда тестирования

```bash
python manage.py test_ethereum
```

Эта команда проверяет:
- Настройки Ethereum
- Наличие валют в базе данных
- Системные кошельки
- Работу Ethereum сервиса

## Безопасность

### Важные моменты

1. **Приватные ключи**: Никогда не храните приватные ключи в открытом виде
2. **RPC провайдеры**: Используйте надежных провайдеров (Infura, Alchemy)
3. **Gas цены**: Настройте разумные лимиты для предотвращения высоких комиссий
4. **Тестирование**: Всегда тестируйте на testnet перед продакшеном

### Рекомендации для продакшена

1. Используйте аппаратные кошельки для системных средств
2. Настройте мониторинг транзакций
3. Реализуйте многоподписные кошельки
4. Регулярно обновляйте зависимости

## Поддерживаемые сети

- **Mainnet**: Основная сеть Ethereum
- **Goerli**: Тестовая сеть (рекомендуется для разработки)
- **Sepolia**: Альтернативная тестовая сеть

## Поддерживаемые токены

### Стандартные ERC-20 токены

- **USDT**: Tether USD
- **USDC**: USD Coin
- **DAI**: Dai Stablecoin
- **LINK**: Chainlink
- **UNI**: Uniswap

### Добавление новых токенов

1. Добавьте токен в модель `Cryptocurrency`
2. Укажите `network='ERC20'`
3. Добавьте `contract_address`
4. Укажите правильное количество `decimals`

## Мониторинг

### Celery задачи

- `check_blockchain_deposits`: Сканирует новые депозиты каждые 30 секунд
- `process_pending_withdrawals`: Обрабатывает выводы каждую минуту

### Логирование

Все операции логируются в Django логи с уровнем INFO/ERROR.

## Устранение неполадок

### Частые проблемы

1. **ModuleNotFoundError**: Убедитесь, что все зависимости установлены
2. **Connection Error**: Проверьте RPC URL и доступность сети
3. **Gas Estimation Failed**: Проверьте настройки газа
4. **Invalid Address**: Убедитесь в правильности Ethereum адресов

### Отладка

```python
import logging
logging.getLogger('crypto.blockchain.ethereum').setLevel(logging.DEBUG)
```

## Обновления

При обновлении интеграции:

1. Обновите зависимости в requirements.txt
2. Запустите миграции базы данных
3. Обновите настройки в .env файлах
4. Протестируйте на testnet
5. Обновите документацию