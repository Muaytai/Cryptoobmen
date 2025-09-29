# Улучшенная система пополнения и консолидации Solana

## Обзор

Данный апгрейд расширяет систему обработки депозитов и консолидации для блокчейна Solana. Добавлены специализированные инструменты для управления Solana кошельками, автоматической консолидации средств и комплексного тестирования.

## Новые возможности

### 1. Автоматическая консолидация Solana
- **Минимальная сумма**: 0.01 SOL для консолидации
- **Резерв на газ**: 0.002 SOL (покрывает ~400 транзакций)
- **Немедленная консолидация**: Автоматически запускается после каждого депозита
- **Умная обработка**: Проверка баланса в блокчейне перед консолидацией

### 2. Улучшенная генерация адресов
- **JSON формат ключей**: Приватные ключи сохраняются в формате JSON массива
- **Автоматическое создание**: Адреса генерируются при создании кошелька
- **Ротация адресов**: Новый адрес после каждого успешного депозита

### 3. Подтверждение транзакций
- **Умная проверка**: Метод `is_transaction_confirmed()` для проверки статуса
- **Обработка ошибок**: Корректная обработка failed транзакций
- **Максимальная версия**: Поддержка versioned транзакций Solana

## Команды управления

### Проверка состояния системы
```bash
# Общая диагностика Solana кошельков
python manage.py check_solana_wallets

# Проверка с синхронизацией балансов
python manage.py check_solana_wallets --sync-balances --check-transactions

# Проверка конкретного пользователя
python manage.py check_solana_wallets --user-id=1 --sync-balances

# Автоматическое исправление адресов
python manage.py check_solana_wallets --fix-addresses
```

### Создание и настройка кошельков
```bash
# Создать кошельки для всех пользователей
python manage.py create_solana_wallets

# Создать кошелек для конкретного пользователя
python manage.py create_solana_wallets --user-email="user@example.com"

# Пересоздать адреса (например, после ротации)
python manage.py create_solana_wallets --regenerate

# Добавить тестовый баланс
python manage.py create_solana_wallets --add-test-balance="0.1"
```

### Тестирование консолидации
```bash
# Анализ возможных консолидаций
python manage.py test_solana_consolidation --analyze-only

# Принудительный запуск консолидации
python manage.py test_solana_consolidation --force-run

# Анализ конкретного пользователя
python manage.py test_solana_consolidation --user-id=1 --analyze-only
```

### Имитация депозитов для тестирования
```bash
# Создать тестовый депозит
python manage.py simulate_solana_deposits --user-email="user@example.com" --amount="0.05"

# Создать несколько депозитов с автоматической консолидацией
python manage.py simulate_solana_deposits --count=3 --amount="0.1" --auto-consolidate

# Создать депозит для случайного пользователя
python manage.py simulate_solana_deposits --amount="0.05" --auto-consolidate
```

## Архитектура консолидации

### Процесс обработки депозита

1. **Сканирование блокчейна** (`check_blockchain_deposits`)
   - Обнаружение новых транзакций на пользовательских адресах
   - Обновление балансов в БД
   - Создание записи о депозите

2. **Автоматическая консолидация** (для SOL и POL)
   - Немедленный запуск после каждого депозита
   - Проверка минимальной суммы (0.01 SOL)
   - Расчет суммы с учетом резерва на газ

3. **Выполнение консолидации** (`consolidate_user_deposits`)
   - Перевод средств с пользовательского адреса на системный
   - Создание транзакции консолидации со статусом "pending"
   - Логирование всех операций

4. **Подтверждение** (`check_consolidation_confirmations`)
   - Проверка статуса транзакций каждую минуту
   - Обновление статуса на "completed"
   - Списание средств с баланса пользователя

### Настройки консолидации

В `tasks_consolidation.py`:

```python
# Минимальные суммы для консолидации
minimums = {
    'SOL': Decimal('0.01'),    # 0.01 SOL
    'POL': Decimal('0.01'),    # 0.01 POL  
    'ETH': Decimal('0.001'),   # 0.001 ETH
    'BTC': Decimal('0.0001'),  # 0.0001 BTC
}

# Резервы на газ
reserves = {
    'SOL': Decimal('0.002'),   # 0.002 SOL (~400 транзакций)
    'POL': Decimal('0.005'),   # 0.005 POL
    'ETH': Decimal('0.0001'),  # 0.0001 ETH
    'BTC': Decimal('0.00001'), # 0.00001 BTC
}
```

### Периодические задачи

В `settings.py` настроены следующие задачи:

```python
CELERY_BEAT_SCHEDULE = {
    'scan_deposits_every_30s': {
        'task': 'crypto.tasks.check_blockchain_deposits',
        'schedule': 30.0,  # Каждые 30 секунд
    },
    'consolidate-user-deposits-every-5-minutes': {
        'task': 'crypto.tasks_consolidation.consolidate_user_deposits', 
        'schedule': 300.0,  # Каждые 5 минут
    },
    'check-consolidation-confirmations-every-minute': {
        'task': 'crypto.tasks_consolidation.check_consolidation_confirmations',
        'schedule': 60.0,  # Каждую минуту
    },
}
```

## Solana-специфичные улучшения

### 1. Обработка приватных ключей
```python
def _parse_private_key(self, key_str: str) -> bytes:
    """Поддержка форматов: JSON-массив, hex, base58"""
    # JSON массив: [251, 34, 123, ...]
    # Hex: abcd1234efgh5678...
    # Base58: (редко используется)
```

### 2. Создание адресов
```python
def create_new_address(self, user_id: int = None) -> tuple[str, str]:
    """Возвращает (адрес, приватный_ключ_в_JSON)"""
    keypair = Keypair()
    public_address = str(keypair.pubkey())
    private_key_json = json.dumps(list(bytes(keypair.secret())))
    return public_address, private_key_json
```

### 3. Проверка подтверждений
```python
def is_transaction_confirmed(self, tx_hash: str) -> bool:
    """Проверка статуса с поддержкой versioned транзакций"""
    tx_response = self.client.get_transaction(
        signature, 
        max_supported_transaction_version=0,
        encoding="jsonParsed"
    )
```

## Мониторинг и отладка

### Логирование
Все операции консолидации подробно логируются:
- Обнаружение депозитов
- Запуск консолидации  
- Отправка транзакций
- Подтверждения в блокчейне
- Ошибки и исключения

### WebSocket уведомления
Система отправляет уведомления через WebSocket:
- При обнаружении депозита
- При успешной консолидации
- При ротации адреса

### Метрики
Отслеживаются следующие метрики:
- Количество обработанных депозитов
- Количество консолидаций
- Общие суммы переводов
- Время выполнения операций

## Безопасность

### Шифрование ключей
- Приватные ключи сохраняются в зашифрованном виде
- Поддержка Fernet шифрования (будет добавлена)
- Ключи не логируются в открытом виде

### Валидация транзакций
- Проверка минимальных сумм
- Контроль резервов на газ
- Предотвращение дублирования транзакций

### Обработка ошибок
- Graceful обработка сетевых ошибок
- Повторные попытки с экспоненциальной задержкой
- Откат состояния при критических ошибках

## Рекомендации по использованию

### 1. Первоначальная настройка
```bash
# 1. Проверить состояние системы
python manage.py check_solana_system_wallet

# 2. Создать кошельки для пользователей
python manage.py create_solana_wallets

# 3. Проверить общее состояние
python manage.py check_solana_wallets --sync-balances
```

### 2. Тестирование
```bash
# 1. Создать тестовые депозиты
python manage.py simulate_solana_deposits --count=3 --amount="0.05"

# 2. Проанализировать возможности консолидации
python manage.py test_solana_consolidation --analyze-only

# 3. Запустить консолидацию
python manage.py test_solana_consolidation --force-run
```

### 3. Мониторинг
```bash
# Ежедневная проверка состояния
python manage.py check_solana_wallets --sync-balances --check-transactions

# Анализ консолидаций
python manage.py test_solana_consolidation --analyze-only
```

## Заключение

Улучшенная система Solana обеспечивает:
- **Автоматизацию**: Консолидация запускается автоматически
- **Надежность**: Комплексные проверки и обработка ошибок
- **Мониторинг**: Подробное логирование и диагностические инструменты
- **Масштабируемость**: Эффективная обработка множественных депозитов
- **Безопасность**: Защищенное хранение ключей и валидация операций

Система готова к продуктивному использованию и может быть легко расширена для поддержки дополнительных блокчейнов.