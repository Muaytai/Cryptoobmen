import random
from django.utils import timezone
from datetime import timedelta
from .models import Cryptocurrency, SystemWalletAddress, UserDepositMemo, UserWallet
from .blockchain.factory import get_blockchain_service
import segno
import io
import base64
import logging

logger = logging.getLogger(__name__)

def generate_qr_code(data: str) -> str:
    """Генерирует QR-код и возвращает его в виде base64 строки."""
    qr = segno.make(data)
    buf = io.BytesIO()
    qr.save(buf, kind='png', scale=6)
    base64_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f'data:image/png;base64,{base64_str}'

class DepositService:

    @staticmethod
    def get_deposit_info(user, currency_symbol, network):
        """
        Возвращает адрес для пополнения.
        - Для валют с MEMO: системный адрес + уникальный memo.
        - Для валют без MEMO: уникальный адрес пользователя, который меняется после использования.
        Также возвращает qr_code (base64 PNG).
        """
        try:
            # 1. Найти валюту с учетом сети
            currency = Cryptocurrency.objects.get(
                symbol__iexact=currency_symbol, 
                network__iexact=network,
                is_active=True
            )

            if currency.requires_memo:
                # --- Логика для валют с MEMO ---
                system_wallet = SystemWalletAddress.objects.get(currency=currency)
                address = system_wallet.address
                if not address:
                    raise ValueError(f"Системный адрес для {currency_symbol} в сети {network} не настроен.")

                memo = DepositService._generate_unique_memo()
                expires_at = timezone.now() + timedelta(hours=24)
                UserDepositMemo.objects.create(
                    user=user, currency=currency, network=network, memo=memo, expires_at=expires_at
                )
                
                # Для некоторых сетей (например, XRP) QR-код может включать доп. параметры
                qr_data = f"{address}?dt={memo}" if currency.symbol == 'XRP' else f"{address}:{memo}"
                qr_code = generate_qr_code(qr_data)
                return address, memo, qr_code
            else:
                # --- Логика для валют без MEMO (BTC, USDT TRC-20 и т.д.) ---
                user_wallet, _ = UserWallet.objects.get_or_create(user=user, currency=currency)
                

                blockchain_service = get_blockchain_service(currency.network or currency.symbol)
                
                # Проверяем, нужно ли генерировать новый адрес.
                # Условия:
                # 1. Адреса еще нет.
                # 2. Адрес уже был использован (на него есть транзакции).
                needs_new_address = False

                if not user_wallet.deposit_address:
                    needs_new_address = True
                    logger.info(f"User {user.id} needs new {currency.symbol} address because none exists.")
                else:
                    try:
                        # Проверяем наличие транзакций на текущем адресе
                        existing_txs = blockchain_service.get_transactions(address=user_wallet.deposit_address)
                        if existing_txs:
                            needs_new_address = True
                            logger.info(f"User {user.id} needs new {currency.symbol} address because the old one has transactions.")
                    except Exception as e:
                        logger.error(f"Failed to check transactions for address {user_wallet.deposit_address}: {e}", exc_info=True)
                        # В случае ошибки не генерируем новый адрес, чтобы избежать проблем
                        needs_new_address = False

                if needs_new_address:
                    try:
                        new_address, private_key = blockchain_service.create_new_address(user_id=user.id)
                        if not new_address:
                            raise ValueError(f"Blockchain service for {network} failed to generate an address.")
                        
                        user_wallet.deposit_address = new_address
                        # Мы должны шифровать приватный ключ перед сохранением!
                        # Пока что сохраняем как есть, но это требует улучшения безопасности.
                        user_wallet.encrypted_private_key = private_key
                        user_wallet.save()
                        logger.info(f"Successfully generated and saved new address for user {user.id}, currency {currency.symbol}.")
                    except Exception as e:
                        logger.error(f"Critical error generating address for {currency.symbol} (user {user.id}): {e}", exc_info=True)
                        raise ValueError(f"Could not generate a new deposit address. Error: {e}")
                
                final_address = user_wallet.deposit_address
                qr_code = generate_qr_code(final_address)
                return final_address, None, qr_code

        except Cryptocurrency.DoesNotExist:
            raise ValueError(f"Криптовалюта {currency_symbol} в сети {network} не найдена или неактивна.")
        except SystemWalletAddress.DoesNotExist:
            raise ValueError(f"Системный кошелек для {currency_symbol} в сети {network} не найден.")
        except Exception as e:
            logger.error(f"Unexpected error in get_deposit_info for user {user.id}: {e}", exc_info=True)
            raise

    @staticmethod
    def _generate_unique_memo():
        """Генерирует уникальный числовой Memo, которого еще нет в базе."""
        while True:
            memo = str(random.randint(100000, 999999))
            if not UserDepositMemo.objects.filter(memo=memo, status='waiting').exists():
                return memo
