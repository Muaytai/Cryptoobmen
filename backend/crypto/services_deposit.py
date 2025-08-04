import random
from django.utils import timezone
from datetime import timedelta
from .models import Cryptocurrency, SystemWalletAddress, UserDepositMemo, UserWallet
from .blockchain.factory import get_blockchain_service
import segno
import io
import base64
from PIL import Image

def generate_qr_code(data: str) -> str:
    qr = segno.make(data)
    buf = io.BytesIO()
    qr.save(buf, kind='png', scale=6)
    base64_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f'data:image/png;base64,{base64_str}'

class DepositService:

    @staticmethod
    def get_deposit_info(user, currency_symbol, network):
        """
        Возвращает адрес для пополнения: если требуется MEMO — системный адрес + memo, иначе уникальный адрес пользователя.
        Также возвращает qr_code (base64 PNG).
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

            if not address:
                return None, None, None

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
                # Генерируем QR-код: адрес + MEMO (например, через \n)
                qr_data = f"{address}:{memo}"
                qr_code = generate_qr_code(qr_data)
                return address, memo, qr_code
            else:
                # Для валют без MEMO — возвращаем или генерируем уникальный адрес пользователя
                user_wallet, _ = UserWallet.objects.get_or_create(user=user, currency=currency)
                
                if not user_wallet.deposit_address:
                    # Адреса нет - генерируем новый
                    try:
                        blockchain_service = get_blockchain_service(network)
                        new_address = blockchain_service.create_new_address(user_id=user.id)
                        user_wallet.deposit_address = new_address
                        user_wallet.save()
                    except Exception as e:
                        raise ValueError(f"Не удалось сгенерировать новый адрес для {currency.symbol}.")
                # Генерируем QR-код только по адресу
                qr_code = generate_qr_code(user_wallet.deposit_address)
                return user_wallet.deposit_address, None, qr_code

        except SystemWalletAddress.DoesNotExist:
            raise ValueError(f"Системный кошелек для {currency_symbol} в сети {network} не найден или неактивен.")
        except Exception as e:
            return None, None, None

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
