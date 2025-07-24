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
            # 1. Найти валюту
            currency = Cryptocurrency.objects.get(symbol__iexact=currency_symbol, is_active=True)

            if currency.requires_memo:
                # Логика для валют с MEMO
                system_wallet = SystemWalletAddress.objects.select_related('currency').get(
                    currency=currency,
                    network__iexact=network
                )
                address = system_wallet.address
                if not address:
                    raise ValueError(f"Системный адрес для {currency_symbol} в сети {network} не настроен.")

                memo = DepositService._generate_unique_memo()
                expires_at = timezone.now() + timedelta(hours=24)
                UserDepositMemo.objects.create(
                    user=user,
                    currency=currency,
                    network=network,
                    memo=memo,
                    expires_at=expires_at
                )
                qr_data = f"{address}:{memo}"
                qr_code = generate_qr_code(qr_data)
                return address, memo, qr_code
            else:
                # Логика для валют без MEMO (например, Bitcoin)
                user_wallet, _ = UserWallet.objects.get_or_create(user=user, currency=currency)

                # Проверяем, нужно ли пересоздать адрес
                # Это нужно, если адреса нет, или если это testnet и адрес не в формате bech32 (не начинается с tb1)
                is_testnet = network.lower() == 'testnet'
                is_invalid_testnet_address = (
                    is_testnet and
                    currency.symbol == 'BTC' and
                    user_wallet.deposit_address and
                    not user_wallet.deposit_address.startswith('tb1')
                )

                if not user_wallet.deposit_address or is_invalid_testnet_address:
                    try:
                        blockchain_service = get_blockchain_service(network)
                        # Для BTC в testnet мы передаем специальный флаг, если это необходимо
                        new_address = blockchain_service.create_new_address(user_id=user.id)
                        if not new_address:
                            raise ValueError(f"Сервис блокчейна для сети {network} не смог сгенерировать адрес.")
                        user_wallet.deposit_address = new_address
                        user_wallet.save()
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"Критическая ошибка при генерации адреса для {currency.symbol} ({user.id}): {e}", exc_info=True)
                        raise ValueError(f"Не удалось сгенерировать новый адрес. Ошибка: {e}")
                
                qr_code = generate_qr_code(user_wallet.deposit_address)
                return user_wallet.deposit_address, None, qr_code

        except Cryptocurrency.DoesNotExist:
            raise ValueError(f"Криптовалюта {currency_symbol} не найдена или неактивна.")
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
