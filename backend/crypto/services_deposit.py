
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
        Также возвращает qr_code (base64 PNG) и информацию о газе для валют без мемо.
        """
        try:
            # 1. Найти валюту с учетом сети
            currency = Cryptocurrency.objects.get(
                symbol__iexact=currency_symbol, 
                network__iexact=network,
                is_active=True
            )
            
            logger.info(f"Found currency: {currency.symbol} (ID: {currency.id}), network: {currency.network}, requires_memo: {currency.requires_memo}")

            if currency.requires_memo:
                # --- Логика для валют с MEMO ---
                logger.info(f"Processing currency with memo: {currency.symbol} (network: {network})")
                system_wallet = SystemWalletAddress.objects.get(currency=currency)
                address = system_wallet.address
                if not address:
                    raise ValueError(f"Системный адрес для {currency_symbol} в сети {network} не настроен.")

                memo = DepositService._generate_unique_memo()
                logger.info(f"Generated memo for {currency.symbol}: {memo}")
                expires_at = timezone.now() + timedelta(hours=24)
                UserDepositMemo.objects.create(
                    user=user, currency=currency, network=network, memo=memo, expires_at=expires_at
                )
                
                # Для XRP QR-код должен содержать адрес и destination tag в формате ripple:ADDRESS?dt=TAG
                # Для других валют с memo используем формат ADDRESS:MEMO
                if currency.symbol == 'XRP':
                    # XRP использует destination tag (dt) в URI формате
                    qr_data = f"ripple:{address}?dt={memo}"
                else:
                    # Для других валют (например, BNB) используем формат ADDRESS:MEMO
                    qr_data = f"{address}:{memo}"
                qr_code = generate_qr_code(qr_data)
                logger.info(f"Returning deposit info for {currency.symbol}: address={address}, memo={memo}")
                return address, memo, qr_code, None  # Нет информации о газе для валют с мемо
            else:
                # --- Логика для валют без MEMO (BTC, USDT TRC-20 и т.д.) ---
                user_wallet, _ = UserWallet.objects.get_or_create(user=user, currency=currency)
                
                blockchain_service = get_blockchain_service(currency.network or currency.symbol)
                
                # УПРОЩЕННАЯ ЛОГИКА: Генерируем адрес только если его нет
                # Без консолидации адреса можно переиспользовать
                needs_new_address = not user_wallet.deposit_address
                
                if needs_new_address:
                    logger.info(f"User {user.id} needs new {currency.symbol} address because none exists.")
                else:
                    logger.info(f"User {user.id} can reuse {currency.symbol} address {user_wallet.deposit_address}")

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
                        
                        # Записываем сгенерированный кошелек в GeneratedWallet
                        from crypto.models import GeneratedWallet
                        GeneratedWallet.record_generated_wallet(
                            address=new_address,
                            private_key=private_key,
                            currency=currency,
                            network=network,
                            user=user,
                            wallet_type='user',
                            created_by='DepositService.get_deposit_info',
                            notes=f'Generated for deposit request by user {user.id}'
                        )
                        
                        # Создаем ожидающую транзакцию депозита
                        from transactions.models import Transaction, Deposit
                        from django.db import transaction as db_transaction
                        
                        with db_transaction.atomic():
                            # Создаем транзакцию со статусом "ожидает подтверждения"
                            transaction_obj = Transaction.objects.create(
                                user=user,
                                type='deposit',
                                status='awaiting_confirmation',
                                amount=0,  # Пока 0, будет обновлено при поступлении средств
                                fee=0,
                                crypto=currency,
                                notes=f"Pending deposit to address {new_address}"
                            )
                            
                            # Создаем объект депозита
                            deposit_obj = Deposit.objects.create(
                                user=user,
                                transaction=transaction_obj,
                                wallet=user_wallet,
                                address=new_address,
                                confirmed=False
                            )
                            
                            logger.info(f"Created pending deposit transaction {transaction_obj.id} for address {new_address}")
                        
                        logger.info(f"Successfully generated and saved new address for user {user.id}, currency {currency.symbol}.")
                    except Exception as e:
                        logger.error(f"Critical error generating address for {currency.symbol} (user {user.id}): {e}", exc_info=True)
                        raise ValueError(f"Could not generate a new deposit address. Error: {e}")
                
                final_address = user_wallet.deposit_address
                qr_code = generate_qr_code(final_address)
                
                # Рассчитываем информацию о газе для валют без мемо
                gas_info = DepositService._calculate_gas_info(currency, blockchain_service, final_address)
                
                return final_address, None, qr_code, gas_info

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

    @staticmethod
    def _calculate_gas_info(currency, blockchain_service, address):
        """
        Рассчитывает информацию о газе для валют без мемо.
        Возвращает словарь с информацией о газе или None если расчет невозможен.
        """
        try:
            # Получаем адрес системного кошелька для расчета газа
            from .tasks_consolidation import get_system_wallet_address
            system_wallet_address = get_system_wallet_address(currency)
            
            # Проверяем, поддерживает ли сервис расчет максимальной отправляемой суммы
            if hasattr(blockchain_service, 'get_max_sendable_amount'):
                # Для валют с умным расчетом газа (например, POL)
                max_sendable = blockchain_service.get_max_sendable_amount(address, system_wallet_address)
                if max_sendable > 0:
                    # Получаем текущий баланс
                    current_balance = blockchain_service.get_balance(address)
                    gas_cost = current_balance - max_sendable
                    
                    return {
                        'estimated_gas_cost': str(gas_cost),
                        'current_balance': str(current_balance),
                        'max_sendable_after_gas': str(max_sendable),
                        'currency_symbol': currency.symbol,
                        'calculation_method': 'smart'
                    }
            
            # Fallback для валют без умного расчета газа
            if hasattr(blockchain_service, 'estimate_gas_cost'):
                # Для валют с методом оценки газа (например, ETH)
                try:
                    # Конвертируем небольшое количество для оценки
                    from decimal import Decimal
                    test_amount = Decimal('0.001')
                    
                    # Конвертируем в атомарные единицы для оценки
                    if hasattr(blockchain_service, 'to_atomic_unit'):
                        test_amount_atomic = blockchain_service.to_atomic_unit(test_amount, currency.decimals or 18)
                    else:
                        test_amount_atomic = int(test_amount * (10 ** (currency.decimals or 18)))
                    
                    gas_cost = blockchain_service.estimate_gas_cost(address, system_wallet_address, test_amount_atomic)
                    
                    return {
                        'estimated_gas_cost': str(gas_cost),
                        'currency_symbol': currency.symbol,
                        'calculation_method': 'estimated'
                    }
                except Exception as e:
                    logger.warning(f"Failed to estimate gas cost for {currency.symbol}: {e}")
            
            # Fallback к фиксированным значениям из tasks_consolidation
            from .tasks_consolidation import get_gas_reserve
            gas_reserve = get_gas_reserve(currency)
            
            return {
                'estimated_gas_cost': str(gas_reserve),
                'currency_symbol': currency.symbol,
                'calculation_method': 'fixed_reserve'
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate gas info for {currency.symbol}: {e}")
            return None

