import random
from django.utils import timezone
from datetime import timedelta
from .models import Cryptocurrency, SystemWalletAddress, UserDepositMemo

class DepositService:

    @staticmethod
    def get_deposit_info(user, currency_symbol, network):
        """
        Возвращает адрес системного кошелька и уникальный Memo для пополнения.
        """
        try:
            # 1. Найти криптовалюту по символу (берём первую активную запись, если их несколько)
            currencies_qs = Cryptocurrency.objects.filter(symbol__iexact=currency_symbol, is_active=True)
            if not currencies_qs.exists():
                raise ValueError(f"Криптовалюта {currency_symbol} не найдена или неактивна.")
            currency = currencies_qs.first()

            # 2. Найти системный адрес для этой валюты и сети
            system_wallet = SystemWalletAddress.objects.get(currency=currency, network__iexact=network)
            address = system_wallet.address

            # 3. Сгенерировать уникальный Memo
            memo = DepositService._generate_unique_memo()

            # 4. Сохранить Memo в базу
            expires_at = timezone.now() + timedelta(hours=24)  # Memo действителен 24 часа
            UserDepositMemo.objects.create(
                user=user,
                currency=currency,
                network=network,
                memo=memo,
                expires_at=expires_at
            )

            return address, memo

        except Cryptocurrency.DoesNotExist:
            raise ValueError(f"Криптовалюта {currency_symbol} не найдена или неактивна.")
        except SystemWalletAddress.DoesNotExist:
            # Возвращаем None, если системный кошелек еще не настроен
            return None, None
        except Exception as e:
            # В реальном проекте здесь будет логирование
            raise e

    @staticmethod
    def _generate_unique_memo():
        """
        Генерирует уникальный числовой Memo, которого еще нет в базе.
        """
        while True:
            # Генерируем случайное 6-значное число
            memo = str(random.randint(100000, 999999))
            # Проверяем, что такого Memo еще не существует
            if not UserDepositMemo.objects.filter(memo=memo).exists():
                return memo 