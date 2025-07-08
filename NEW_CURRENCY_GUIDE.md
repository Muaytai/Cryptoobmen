# Руководство по добавлению новой криптовалюты

Это руководство описывает шаги, необходимые для интеграции новой криптовалюты или токена в проект Cryptoobmen.

---

## Шаг 1: Добавление валюты в базу данных

Вся информация о поддерживаемых валютах хранится в модели `Cryptocurrency`.

1.  **Войдите в админ-панель Django** (`/admin/`).
2.  Перейдите в раздел "Crypto" -> "Currencies".
3.  Нажмите "Add currency" и заполните поля:
    *   **Name:** Полное название валюты (например, `Ethereum`).
    *   **Symbol:** Тикер валюты (например, `ETH`).
    *   **Currency Type:** `Cryptocurrency`.
    *   **Network:** Название сети, которое будет использоваться для идентификации сервиса (например, `ETH`, `ERC20`, `MATIC`). Это название должно быть уникальным для связки символ+сеть.
    *   **Decimals:** Количество знаков после запятой (например, `18` для ETH и большинства токенов ERC20).
    *   **Requires Memo:** **Очень важное поле!**
        *   Отметьте галочкой, если для пополнения счета в этой валюте требуется `Memo` или `Destination Tag` (например, для `USDT (TRC20)`).
        *   Оставьте пустым для валют, которые не используют `memo` (например, `Bitcoin`, `Ethereum`).
    *   Остальные поля (иконка, ID для CoinGecko и т.д.) заполните по необходимости.

## Шаг 2: Создание сервиса для блокчейна

Для каждой новой сети необходимо создать сервис, который будет обрабатывать логику взаимодействия с ее блокчейном.

1.  В директории `backend/crypto/blockchain/` создайте новый файл, например, `ethereum_service.py`.
2.  В этом файле создайте класс, который наследуется от `BaseBlockchainService`.
3.  Реализуйте три обязательных метода: `get_balance`, `get_transactions`, `send_transaction`.

**Пример-скелет для `ethereum_service.py`:**
```python
from decimal import Decimal
from typing import List, Dict, Any
from .base import BaseBlockchainService

class EthereumService(BaseBlockchainService):
    def __init__(self, network: str = 'mainnet'):
        super().__init__(network)
        # Здесь ваша логика инициализации (например, подключение к Web3)

    def get_balance(self, address: str) -> Decimal:
        # Реализуйте логику получения баланса для ETH или токенов ERC20
        raise NotImplementedError("get_balance is not implemented yet")

    def get_transactions(self, address: str, min_timestamp: int = 0) -> List[Dict[str, Any]]:
        # Реализуйте логику получения входящих транзакций
        raise NotImplementedError("get_transactions is not implemented yet")

    def send_transaction(self, private_key: str, to_address: str, amount: Decimal, memo: str = "") -> str:
        # Реализуйте логику отправки транзакции
        # Помните, что memo здесь, скорее всего, не будет использоваться
        raise NotImplementedError("send_transaction is not implemented yet")
```

## Шаг 3: Регистрация нового сервиса в "фабрике"

"Фабрика" (`factory.py`) отвечает за выбор нужного сервиса в зависимости от сети.

1.  Откройте файл `backend/crypto/blockchain/factory.py`.
2.  Импортируйте ваш новый сервис: `from .ethereum_service import EthereumService`.
3.  Добавьте новую ветку в условном операторе `if/elif/else`:

```python
# ... другие импорты
from .ethereum_service import EthereumService

def get_blockchain_service(network: str) -> BaseBlockchainService:
    network_lower = network.lower()
    
    if network_lower == 'tron' or network_lower == 'trc20':
        return TronService(network='nile') # или 'mainnet'
    
    elif network_lower == 'btc' or network_lower == 'bitcoin':
        return BitcoinService(network='testnet') # или 'mainnet'

    # >>> ВАШ КОД ЗДЕСЬ <<<
    elif network_lower == 'eth' or network_lower == 'erc20':
        return EthereumService(network='mainnet')

    else:
        raise ValueError(f"Unsupported blockchain network: {network}")
```
**Важно:** Строка, которую вы проверяете (`'eth'`, `'erc20'`), должна совпадать со значением поля `Network` из Шага 1.

## Шаг 4: Настройка системного кошелька для вывода средств

Система использует специальные кошельки для отправки средств пользователям (выводы).

1.  В админ-панели перейдите в раздел "Crypto" -> "Wallets".
2.  Нажмите "Add wallet" и заполните:
    *   **User:** Оставьте это поле пустым.
    *   **Currency:** Выберите новую валюту, которую вы добавили.
    *   **Is System Wallet:** **Обязательно поставьте галочку!**
    *   **Encrypted Private Key:** Вставьте **приватный ключ** от вашего системного кошелька для этой валюты. На данный момент ключ не шифруется, но поле называется так с заделом на будущее.
    *   **Is Active:** Убедитесь, что галочка стоит.
3.  Сохраните кошелек.

## Шаг 5: Настройка адреса для приема депозитов

1.  В админ-панели перейдите в раздел "Crypto" -> "System Wallet Addresses".
2.  Нажмите "Add system wallet address" и заполните:
    *   **Currency:** Выберите новую валюту.
    *   **Network:** Укажите ту же сеть, что и в Шаге 1.
    *   **Address:** Вставьте **публичный адрес** вашего системного кошелька.
3.  Сохраните адрес.

---

После выполнения этих шагов новая криптовалюта будет интегрирована в систему. Фоновые задачи для обработки выводов и депозитов (с `memo`) должны заработать автоматически.
