"""
Management command to check the status of Solana deposits and wallets.
"""
import logging
from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, UserWallet
from crypto.blockchain.factory import get_blockchain_service
from transactions.models import Transaction

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Check the status of Solana deposits and wallets"

    def handle(self, *args, **options):
        self.stdout.write('Checking Solana deposit system status...')
        
        # Get Solana currency
        try:
            sol_currency = Cryptocurrency.objects.get(symbol='SOL', network='solana')
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Solana currency not found in database')
            )
            return

        # Check system wallet
        try:
            system_wallet = UserWallet.objects.get(currency=sol_currency, is_system_wallet=True)
            self.stdout.write(
                self.style.SUCCESS(f'System wallet found: {system_wallet.deposit_address}')
            )
            
            # Check system wallet balance
            try:
                service = get_blockchain_service('solana')
                system_balance = service.get_balance(system_wallet.deposit_address)
                self.stdout.write(
                    self.style.SUCCESS(f'System wallet balance: {system_balance} SOL')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to get system wallet balance: {e}')
                )
                
        except UserWallet.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('System wallet for Solana not found')
            )
            return

        # Check user wallets
        user_wallets = UserWallet.objects.filter(currency=sol_currency, is_system_wallet=False)
        self.stdout.write(f'Found {user_wallets.count()} user wallets for Solana')
        
        # Check for wallets with deposit addresses
        wallets_with_addresses = user_wallets.exclude(deposit_address__isnull=True).exclude(deposit_address='')
        self.stdout.write(f'Found {wallets_with_addresses.count()} user wallets with deposit addresses')
        
        # Check balances
        total_db_balance = 0
        total_blockchain_balance = 0
        
        for wallet in wallets_with_addresses:
            total_db_balance += wallet.balance
            try:
                blockchain_balance = service.get_balance(wallet.deposit_address)
                total_blockchain_balance += blockchain_balance
                if blockchain_balance > 0:
                    self.stdout.write(
                        self.style.WARNING(f'Wallet {wallet.id} ({wallet.deposit_address[:10]}...) has {blockchain_balance} SOL on blockchain but {wallet.balance} SOL in DB')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to get balance for wallet {wallet.id}: {e}')
                )
        
        self.stdout.write(
            self.style.NOTICE(f'Total user balance in DB: {total_db_balance} SOL')
        )
        self.stdout.write(
            self.style.NOTICE(f'Total user balance on blockchain: {total_blockchain_balance} SOL')
        )
        
        # Check recent transactions
        recent_deposits = Transaction.objects.filter(crypto=sol_currency, type='deposit').order_by('-timestamp')[:10]
        self.stdout.write(f'\nRecent deposits:')
        for deposit in recent_deposits:
            self.stdout.write(f'  {deposit.timestamp} - {deposit.amount} SOL - {deposit.tx_hash} - {deposit.status}')
            
        recent_consolidations = Transaction.objects.filter(crypto=sol_currency, type='consolidation').order_by('-timestamp')[:10]
        self.stdout.write(f'\nRecent consolidations:')
        for consolidation in recent_consolidations:
            self.stdout.write(f'  {consolidation.timestamp} - {consolidation.amount} SOL - {consolidation.tx_hash} - {consolidation.status}')