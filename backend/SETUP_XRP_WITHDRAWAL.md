# Настройка вывода XRP

## 1. Создать системный кошелек XRP

```bash
# Для тестирования
python manage.py setup_xrp_system_wallet --network testnet

# Для продакшена  
python manage.py setup_xrp_system_wallet --network mainnet
```

## 2. Проверить настройку

```bash
python manage.py shell
```

```python
from crypto.models import UserWallet, Cryptocurrency

# Проверяем системный кошелек
xrp_currency = Cryptocurrency.objects.get(symbol="XRP", network="XRP")
system_wallet = UserWallet.objects.get(
    user=None, 
    currency=xrp_currency, 
    is_system_wallet=True
)

print(f"Системный кошелек: {system_wallet}")
print(f"Приватный ключ: {'Есть' if system_wallet.encrypted_private_key else 'Отсутствует'}")
```

## 3. Готово!

Теперь можно делать вывод XRP через сайт. Система работает независимо от пополнения. 