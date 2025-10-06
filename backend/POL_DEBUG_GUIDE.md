# Диагностика проблемы с POL депозитами

## Проблема
Депозит 0.2 POL записывается как 0 в базу данных.

## Проведенная диагностика

### ✅ Проверено и работает корректно:
1. **Математика преобразования**: Wei → POL конвертация работает правильно
2. **Настройки валюты**: POL имеет правильные параметры в БД:
   - `decimals=18` ✅
   - `requires_memo=False` ✅ 
   - `network="Polygon"` ✅
3. **Логика маршрутизации**: POL должен обрабатываться во втором блоке (без MEMO)
4. **Тип поля БД**: `DecimalField(max_digits=24, decimal_places=8)` достаточен для 0.2

### 🔍 Добавлено подробное логирование в:
- `crypto/tasks.py` строки 221, 359, 422, 437, 440, 451

## Логи для анализа

При следующем POL депозите ищите в логах:

### 1. Проверка блока MEMO (должен быть пропущен)
```
[INFO] Skipping POL in Polygon: MEMO not required (per official docs). Currency decimals: 18
```

### 2. Начало обработки POL в блоке без MEMO
```
[INFO] [BATCH] Starting batch processing for POL, network=Polygon, decimals=18, requires_memo=False
```

### 3. Преобразование суммы
```
[INFO] [BATCH] Processing amount conversion: currency=POL, network=Polygon, amount_str=200000000000000000, decimals=18
[INFO] [BATCH] Converting 200000000000000000 with 18 decimals to 0.2 POL
[INFO] [BATCH] Amount conversion result: 0.2 POL
```

### 4. Сохранение в БД
```
[INFO] [BATCH] Saving transaction: user=123, currency=POL, amount=0.2, tx_hash=0x...
[INFO] [BATCH] Deposit credited: 123 POL 0.2
```

## Возможные причины проблемы

### 1. POL попадает в неправильный блок
- **Симптом**: В логах нет `[BATCH]` записей для POL
- **Причина**: Возможно, у POL есть `SystemWalletAddress` и он обрабатывается в первом блоке
- **Решение**: Проверить `SystemWalletAddress.objects.filter(currency__symbol='POL')`

### 2. Проблема с получением транзакций из блокчейна
- **Симптом**: `amount_str` приходит как "0" или пустая строка
- **Причина**: Проблема в `polygon.py` при получении `tx.value`
- **Решение**: Проверить логи сканирования блоков

### 3. Проблема с сохранением в БД
- **Симптом**: Логи показывают правильную сумму, но в БД сохраняется 0
- **Причина**: Возможна проблема с типами данных или транзакциями БД
- **Решение**: Проверить Django debug toolbar или прямые SQL запросы

### 4. Дублирование транзакций
- **Симптом**: `Transaction already exists, skipping duplicate`
- **Причина**: Транзакция уже была обработана с неправильной суммой
- **Решение**: Проверить существующие транзакции в БД

## Команды для диагностики

### Проверить последние POL транзакции в БД:
```sql
SELECT id, user_id, amount, tx_hash, timestamp, type, status 
FROM transactions_transaction 
WHERE crypto_id = (SELECT id FROM crypto_cryptocurrency WHERE symbol='POL') 
ORDER BY timestamp DESC 
LIMIT 10;
```

### Проверить настройки POL:
```sql
SELECT name, symbol, network, decimals, requires_memo, is_active 
FROM crypto_cryptocurrency 
WHERE symbol='POL';
```

### Проверить SystemWalletAddress для POL:
```sql
SELECT address, network 
FROM crypto_systemwalletaddress 
WHERE currency_id = (SELECT id FROM crypto_cryptocurrency WHERE symbol='POL');
```

## Следующие шаги

1. **Запустить задачу** `check_blockchain_deposits` и проанализировать логи
2. **Найти конкретное место** где теряется правильная сумма
3. **Исправить проблему** в зависимости от найденной причины

## Контакты для логов

Предоставьте следующие логи для анализа:
- Логи задачи `check_blockchain_deposits` за период депозита
- Логи с префиксами `[BATCH]`, `[POL]`, `[POLYGON]`
- Результат SQL запросов выше
