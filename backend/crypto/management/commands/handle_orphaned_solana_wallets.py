"""
Management command to handle orphaned Solana temporary wallets that have funds
but are not associated with any user in the database.
"""
import logging
from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, UserWallet
from crypto.blockchain.factory import get_blockchain_service

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Handle orphaned Solana temporary wallets with funds"

    def add_arguments(self, parser):
        parser.add_argument(
            '--address',
            type=str,
            help='Specific temporary wallet address to handle',
        )
        parser.add_argument(
            '--private-key',
            type=str,
            help='Private key for the temporary wallet (in JSON format)',
        )
        parser.add_argument(
            '--system-wallet-id',
            type=int,
            help='System wallet ID to transfer funds to (default: auto-detect)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually transferring funds',
        )

    def handle(self, *args, **options):
        # Get Solana currency
        try:
            sol_currency = Cryptocurrency.objects.get(symbol='SOL', network='solana')
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Solana currency not found in database')
            )
            return

        # Get system wallet
        if options['system_wallet_id']:
            try:
                system_wallet = UserWallet.objects.get(id=options['system_wallet_id'], is_system_wallet=True)
            except UserWallet.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'System wallet with ID {options["system_wallet_id"]} not found')
                )
                return
        else:
            try:
                system_wallet = UserWallet.objects.get(currency=sol_currency, is_system_wallet=True)
            except UserWallet.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR('System wallet for Solana not found')
                )
                return

        self.stdout.write(f'System wallet address: {system_wallet.deposit_address}')

        # Get blockchain service
        try:
            service = get_blockchain_service('solana')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to initialize Solana service: {e}')
            )
            return

        # Handle specific address or scan for orphaned wallets
        if options['address']:
            self.handle_specific_address(service, options['address'], options['private_key'], system_wallet, options['dry_run'])
        else:
            self.stdout.write(
                self.style.ERROR('Please specify a wallet address to handle')
            )

    def handle_specific_address(self, service, address, private_key, system_wallet, dry_run):
        """Handle a specific temporary wallet address"""
        self.stdout.write(f'Checking temporary wallet: {address}')
        
        # Get balance
        try:
            balance = service.get_balance(address)
            self.stdout.write(f'Balance: {balance} SOL')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to get balance for {address}: {e}')
            )
            return

        if balance <= 0:
            self.stdout.write(
                self.style.WARNING('Wallet has no funds, nothing to do')
            )
            return

        # Check if private key is provided
        if not private_key:
            self.stdout.write(
                self.style.ERROR('Private key is required to transfer funds')
            )
            return

        # Show what would be done
        self.stdout.write(
            self.style.NOTICE(f'Would transfer {balance} SOL from {address} to {system_wallet.deposit_address}')
        )

        if dry_run:
            self.stdout.write(
                self.style.NOTICE('Dry run mode - no actual transfer performed')
            )
            return

        # Perform the transfer
        try:
            tx_hash = service.send_transaction(
                private_key_input=private_key,
                to_address=system_wallet.deposit_address,
                amount=balance
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully transferred {balance} SOL from {address} to {system_wallet.deposit_address}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'Transaction hash: {tx_hash}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to transfer funds: {e}')
            )