import random
from django.utils import timezone
from datetime import timedelta
from .models import Cryptocurrency, SystemWalletAddress, UserDepositMemo, UserWallet

class DepositService:

    @staticmethod
    def get_deposit_info(user, currency_symbol, network):
        """
        Возвращает адрес для пополнения: если требуется MEMO — системный адрес + memo, иначе уникальный адрес пользователя.
        """
        try:
            # 1. Найти системный адрес для валюты и сети
            system_wallet = SystemWalletAddress.objects.select_related('currency').get(
                currency__symbol__iexact=currency_symbol,
                currency__is_active=True,
                network__iexact=network
            )
            currency = system_wallet.currency
            address = system_wallet.address

            if currency.requires_memo:
                # 2. Сгенерировать уникальный Memo
                memo = DepositService._generate_unique_memo()
                # 3. Сохранить Memo в базу
                expires_at = timezone.now() + timedelta(hours=24)  # Memo действителен 24 часа
                UserDepositMemo.objects.create(
                    user=user,
                    currency=currency,
                    network=network,
                    memo=memo,
                    expires_at=expires_at
                )
                return address, memo
            else:
                # Для валют без MEMO — возвращаем уникальный адрес пользователя
                user_wallet, _ = UserWallet.objects.get_or_create(user=user, currency=currency)
                if not user_wallet.deposit_address:
                    # Вместо генерации тестового адреса выбрасываем ошибку
                    raise ValueError("Для этой валюты и сети не настроена генерация реальных адресов. Обратитесь к администратору.")
                return user_wallet.deposit_address, None

        except SystemWalletAddress.DoesNotExist:
            raise ValueError(f"Системный кошелек для {currency_symbol} в сети {network} не найден или неактивен.")
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