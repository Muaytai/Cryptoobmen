import time
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from crypto.models import (
    Cryptocurrency, SystemWalletAddress, UserDepositMemo, 
    UserWallet, BlockchainState
)
from transactions.models import Transaction
from tronpy import Tron
from tronpy.providers import HTTPProvider
from tronpy.exceptions import ApiError as TronException
from django.conf import settings



class Command(BaseCommand):
    help = 'Listens for new TRC20 deposits and updates balances.'

    def handle(self, *args, **options):
        """Основной цикл команды."""
        self.stdout.write(self.style.SUCCESS('--- Starting TRC20 deposit listener... ---'))
        
        try:
            client = Tron(network='nile', conf={'api_key': settings.TRONGRID_API_KEY})
            client.default_address = 'T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb' # Адрес по умолчанию не важен
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Could not connect to TronGrid: {e}"))
            return

        while True:
            try:
                self.check_usdt_deposits(client)
                self.stdout.write(self.style.SUCCESS("Cycle complete. Waiting for 30 seconds..."))
                time.sleep(30)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"An unexpected error occurred in main loop: {e}"))
                time.sleep(60)

    def check_usdt_deposits(self, client):
        network_name = 'TRC20'
        state, created = BlockchainState.objects.get_or_create(blockchain=network_name)

        # --- Умный старт ---
        latest_block_for_check = client.get_latest_block_number()
        if created or (latest_block_for_check - state.last_processed_block > 5000):
            self.stdout.write(self.style.WARNING(
                f"State is too old (or new). Fast-forwarding to {latest_block_for_check - 200}."
            ))
            state.last_processed_block = latest_block_for_check - 200
            state.save()
        # --- Конец умного старта ---

        last_processed_block = state.last_processed_block
        latest_block = client.get_latest_block_number()

        if latest_block <= last_processed_block:
            return

        self.stdout.write(f"Scanning from block {last_processed_block + 1} to {latest_block}...")

        for block_num in range(last_processed_block + 1, latest_block + 1):
            try:
                block = client.get_block(block_num)
                if not block or 'transactions' not in block:
                    continue

                for tx_summary in block['transactions']:
                    tx_hash = tx_summary['txID']
                    self.process_transaction(tx_hash, client)
                    time.sleep(0.2)

                state.last_processed_block = block_num
                state.save()

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error processing block {block_num}: {e}"))
                state.last_processed_block = block_num
                state.save()

    @transaction.atomic
    def process_transaction(self, tx_hash, client):
        """Обрабатывает одну транзакцию, ища в ней нужный лог."""
        try:
            if Transaction.objects.filter(tx_hash=tx_hash).exists():
                return
            
            tx_data = client.get_transaction(tx_hash)

            if not tx_data or not tx_data.get('raw_data', {}).get('contract'):
                return
            if tx_data['raw_data']['contract'][0]['type'] != 'TriggerSmartContract':
                return

            parameter = tx_data['raw_data']['contract'][0].get('parameter', {}).get('value', {})
            contract_address_hex = parameter.get('contract_address')
            if not contract_address_hex:
                return
            
            contract_address_b58 = client.to_base58check_address(contract_address_hex)

            memo_hex = tx_data['raw_data'].get('data')
            memo = None

            if memo_hex:
                try:
                    memo_bytes = bytes.fromhex(memo_hex)
                    memo = memo_bytes.decode('utf-8', errors='ignore').strip()
                except Exception:
                    memo = None 

            if contract_address_b58 != settings.USDT_CONTRACT_ADDRESS:
                return

            call_data_hex = parameter.get('data', '')
            if not call_data_hex.startswith('a9059cbb'):
                return

            recipient_hex = '41' + call_data_hex[32:72]
            recipient_b58 = client.to_base58check_address(recipient_hex)
            
            system_wallet = SystemWalletAddress.objects.filter(address=recipient_b58).first()

            if not system_wallet:
                return

            deposit_memo = UserDepositMemo.objects.filter(
                memo=memo,
                status='waiting',
                currency=system_wallet.currency,
                network=system_wallet.network
            ).first()

            if not deposit_memo:
                return

            self.stdout.write(self.style.SUCCESS(f"Processing deposit for Memo {memo} in TX {tx_hash}"))
            
            amount_raw = int(call_data_hex[72:136], 16)
            amount = Decimal(amount_raw) / Decimal(10**6)

            user = deposit_memo.user
            user_wallet, _ = UserWallet.objects.get_or_create(user=user, currency=system_wallet.currency)
            
            user_wallet.balance += amount
            user_wallet.save()

            Transaction.objects.create(
                user=user,
                type='deposit',
                status='completed',
                amount=amount,
                crypto=system_wallet.currency,
                tx_hash=tx_hash,
                notes=f"TRC20 Deposit with Memo: {memo}"
            )

            deposit_memo.status = 'used'
            deposit_memo.save()
            
            self.stdout.write(self.style.SUCCESS(f"Credited {amount} {system_wallet.currency.symbol} to {user.email}"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error processing transaction {tx_hash}: {e}")) 