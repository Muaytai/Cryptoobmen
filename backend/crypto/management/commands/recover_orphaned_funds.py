"""
Management command to recover funds from orphaned temporary wallets.
"""
import logging
import json
from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, UserWallet
from crypto.blockchain.factory import get_blockchain_service

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Recover funds from orphaned temporary wallets"

    def add_arguments(self, parser):
        parser.add_argument(
            '--address',
            type=str,
            required=True,
            help='Temporary wallet address with orphaned funds',
        )
        parser.add_argument(
            '--private-key',
            type=str,
            required=True,
            help='Private key for the temporary wallet (JSON array format)',
        )
        parser.add_argument(
            '--currency',
            type=str,
            default='SOL',
            help='Currency symbol (default: SOL)',
        )
        parser.add_argument(
            '--network',
            type=str,
            default='solana',
            help='Network (default: solana)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually transferring funds',
        )

    def handle(self, *args, **options):
        address = options['address']
        private_key = options['private_key']
        currency_symbol = options['currency']
        network = options['network']
        dry_run = options['dry_run']
        
        self.stdout.write(f'Recovering funds from orphaned wallet: {address}')
        
        # Validate private key format
        try:
            # Try to parse as JSON array
            key_data = json.loads(private_key)
            if not isinstance(key_data, list) or len(key_data) != 64:
                raise ValueError("Private key must be a JSON array of 64 integers")
        except json.JSONDecodeError:
            self.stdout.write(
                self.style.ERROR('Private key must be in JSON format')
            )
            return
            
        # Get currency
        try:
            currency = Cryptocurrency.objects.get(symbol=currency_symbol, network=network)
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Currency {currency_symbol} on network {network} not found in database')
            )
            return

        # Get system wallet
        try:
            system_wallet = UserWallet.objects.get(currency=currency, is_system_wallet=True)
            if not system_wallet.deposit_address:
                self.stdout.write(
                    self.style.ERROR('System wallet has no deposit address')
                )
                return
        except UserWallet.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('System wallet not found')
            )
            return

        # Get blockchain service
        try:
            service = get_blockchain_service(network)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to initialize {network} service: {e}')
            )
            return

        # Get balance
        try:
            balance = service.get_balance(address)
            self.stdout.write(f'Wallet balance: {balance} {currency_symbol}')
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

        # Show what would be done
        self.stdout.write(
            self.style.NOTICE(f'Would transfer {balance} {currency_symbol} from {address} to {system_wallet.deposit_address}')
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
                self.style.SUCCESS(f'Successfully transferred {balance} {currency_symbol} from {address} to {system_wallet.deposit_address}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'Transaction hash: {tx_hash}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to transfer funds: {e}')
            )
            return
            
        # Also update the user's wallet balance to reflect that funds have been moved
        # This is just for record keeping since the funds were already credited to the user
        self.stdout.write(
            self.style.SUCCESS('Funds recovery completed successfully')
        )