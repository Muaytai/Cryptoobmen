# Сравнение логики вывода средств Solana и Polygon

## 🔍 Анализ проблемы

Из логов видно, что транзакция Solana была успешно отправлена и подтверждена:
- **Hash**: `35Et7u7rvRC2GYSVunU42HmMxU5VL4FkG8fBgt5MwtAvPkp25sFxwwWrBRk2XCvQMiAsw8hP1mUUsPSgcUeHq99s`
- **Статус**: Подтверждена в блокчейне
- **Проблема**: Отправлено с системного кошелька на тот же системный кошелек

## 📊 Сравнение логики вывода

### 1. **Общий процесс (одинаковый для всех валют)**

```python
# backend/crypto/tasks.py:process_withdrawal()
@shared_task(bind=True, name='crypto.tasks.process_withdrawal')
def process_withdrawal(self, withdrawal_id: int) -> str:
    # 1. Получение данных вывода
    withdrawal = Withdrawal.objects.get(id=withdrawal_id)
    
    # 2. Расчет комиссий и сумм
    gas_cost = calculate_withdrawal_gas_cost(...)
    platform_fee = withdrawal.transaction.fee
    total_amount = amount_to_send + platform_fee + gas_cost
    
    # 3. Блокировка средств
    user_wallet.balance -= total_amount
    user_wallet.locked_balance += total_amount
    
    # 4. Отправка в блокчейн
    tx_kwargs = {
        'private_key': system_wallet.encrypted_private_key,
        'to_address': withdrawal.destination_address,  # ← ПРОБЛЕМА ЗДЕСЬ
        'amount': amount_to_send,
        'memo': f"withdrawal_{withdrawal.id}"
    }
    tx_hash = service.send_transaction(**tx_kwargs)
```

### 2. **Различия в блокчейн-сервисах**

| Параметр | Solana | Polygon |
|----------|--------|---------|
| **Сеть** | devnet | testnet (Amoy) |
| **RPC** | Helius | Polygon RPC |
| **Подтверждения** | 1 | Настраиваемые |
| **Gas расчет** | Фиксированный (0.001 SOL) | Динамический |
| **Валидация адреса** | Base58 (44 символа) | Hex (42 символа) |

### 3. **SolanaService.send_transaction()**

```python
def send_transaction(self, private_key_input=None, to_address="", amount=Decimal("0"), memo="", private_key=None):
    # Валидация адреса получателя
    recipient = Pubkey.from_string(to_address)  # ← Валидация работает
    
    # Получение отправителя из приватного ключа
    sender = Keypair.from_bytes(secret_key_bytes)
    sender_address = str(sender.pubkey())
    
    # Логирование (показывает проблему)
    logger.info(f"Отправка {amount} SOL с {sender_address} на {to_address}")
    
    # Создание и отправка транзакции
    transaction = Transaction.new_unsigned(...)
    signed_tx = Keypair.sign_message(keypair, transaction.serialize())
    tx_hash = self.client.send_transaction(signed_tx)
```

### 4. **PolygonService.send_transaction()**

```python
def send_transaction(self, private_key: str, to_address: str, amount: Decimal, memo: str = ""):
    # Валидация адреса
    if not is_address(to_address):
        raise PolygonError(f"Invalid recipient address: {to_address}")
    
    # Создание аккаунта
    account = Account.from_key(private_key)
    from_address = account.address
    
    # Подготовка транзакции
    transaction = {
        'to': to_checksum_address(to_address),
        'value': Web3.to_wei(amount, 'ether'),
        'gas': self.gas_limit,
        'gasPrice': self._get_gas_price(),
        'nonce': self.w3.eth.get_transaction_count(from_address),
        'chainId': self.w3.eth.chain_id
    }
    
    # Подпись и отправка
    signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
    tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
```

## 🚨 Найденная проблема

### **Корень проблемы**: Неправильный `destination_address` в базе данных

Из логов:
```
[send_transaction] Отправка 0.00998000 SOL с GkVvtMDQ5v1ReiScLQAf45B2X3H1WXr8hrJoY7jcqddQ на GkVvtMDQ5v1ReiScLQAf45B2X3H1WXr8hrJoY7jcqddQ
```

**Оба адреса одинаковые!** Это означает:
1. `withdrawal.destination_address` = адрес системного кошелька
2. Система отправляет средства "сама себе"
3. Средства не доходят до пользователя

### **Причина**: Ошибка в создании запроса на вывод

В `WithdrawalService.create_withdrawal_request()`:
```python
withdrawal_obj = Withdrawal.objects.create(
    user=user,
    transaction=transaction_obj,
    wallet=wallet,
    destination_address=destination_address,  # ← Может быть неправильным
    memo=memo,
    ...
)
```

## 🔧 Решение

### 1. **Немедленное исправление**
Запустить скрипт исправления:
```bash
python backend/fix_withdrawal_addresses.py
```

### 2. **Диагностика проблемы**
Запустить скрипт сравнения:
```bash
python backend/compare_withdrawals.py
```

### 3. **Перезапуск обработки**
После исправления перезапустить обработку выводов:
```bash
python manage.py shell -c "from crypto.tasks import process_pending_withdrawals; process_pending_withdrawals()"
```

## 📋 Рекомендации

### **Для предотвращения проблемы в будущем:**

1. **Улучшить валидацию адресов**:
   ```python
   def validate_destination_address(self, address, currency):
       # Проверка, что адрес не является системным кошельком
       system_wallet = UserWallet.objects.get(currency=currency, is_system_wallet=True)
       if address == system_wallet.deposit_address:
           raise ValidationError("Destination address cannot be system wallet")
   ```

2. **Добавить логирование в создание выводов**:
   ```python
   logger.info(f"Creating withdrawal: user={user.email}, destination={destination_address}, amount={amount}")
   ```

3. **Добавить проверку в process_withdrawal**:
   ```python
   if withdrawal.destination_address == system_wallet.deposit_address:
       raise Exception(f"Invalid destination address: cannot send to system wallet")
   ```

### **Мониторинг**:
- Регулярно проверять выводы с одинаковыми адресами отправителя и получателя
- Настроить алерты при обнаружении таких случаев

## ✅ Выводы

1. **Логика вывода идентична** для Solana и Polygon
2. **Проблема не в блокчейн-сервисах**, а в данных базы
3. **Транзакция выполнилась корректно** - просто на неправильный адрес
4. **Исправление возможно** через обновление `destination_address` в базе данных
