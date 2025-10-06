from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, UserWallet
from crypto.blockchain.factory import get_blockchain_service
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Adds test funds to a wallet address'

    def add_arguments(self, parser):
        parser.add_argument(
            '--address',
            type=str,
            required=True,
            help='Address to add funds to',
        )
        parser.add_argument(
            '--amount',
            type=str,
            default='1.0',
            help='Amount of SOL to add (default: 1.0)',
        )
        parser.add_argument(
            '--network',
            type=str,
            default='devnet',
            help='Solana network (default: devnet)',
        )

    def handle(self, *args, **options):
        address = options['address']
        amount = Decimal(options['amount'])
        network = options['network']
        
        self.stdout.write(f"=== Adding test funds to {address} ===")
        self.stdout.write(f"Amount: {amount} SOL")
        self.stdout.write(f"Network: {network}")
        
        try:
            # Find the SOL currency
            try:
                sol_currency = Cryptocurrency.objects.get(symbol__iexact='SOL', network__iexact=network)
                self.stdout.write(self.style.SUCCESS(f"✓ Found SOL currency: {sol_currency}"))
            except Cryptocurrency.DoesNotExist:
                self.stdout.write(self.style.ERROR("✗ SOL currency not found"))
                return

            # Find if this is a system wallet
            try:
                target_wallet = UserWallet.objects.get(
                    deposit_address=address,
                    currency=sol_currency
                )
                self.stdout.write(self.style.SUCCESS(f"✓ Found wallet in database: {target_wallet}"))
                self.stdout.write(f"  Current balance: {target_wallet.balance} SOL")
            except UserWallet.DoesNotExist:
                self.stdout.write(self.style.WARNING("⚠ Wallet not found in database, but will send funds anyway"))
                target_wallet = None

            # Get the Solana service
            try:
                service = get_blockchain_service('solana')
                self.stdout.write(self.style.SUCCESS(f"✓ Initialized Solana service"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Failed to initialize Solana service: {e}"))
                return

            # Validate the address
            if not service.validate_address(address):
                self.stdout.write(self.style.ERROR(f"✗ Invalid address: {address}"))
                return
            self.stdout.write(self.style.SUCCESS("✓ Address is valid"))

            # For devnet, we can create a temporary wallet to send funds from
            self.stdout.write("\n--- Creating temporary test wallet ---")
            try:
                temp_address, temp_private_key = service.create_new_address()
                self.stdout.write(self.style.SUCCESS(f"✓ Created temporary wallet"))
                self.stdout.write(f"  Address: {temp_address}")
                # Note: In devnet, we can get free SOL from the faucet
                self.stdout.write("  Note: You'll need to fund this temporary wallet from Solana devnet faucet")
                self.stdout.write("  Visit: https://solfaucet.com/ to get devnet SOL")
                
                # Save the temporary wallet info
                self.stdout.write(f"\n--- IMPORTANT ---")
                self.stdout.write(f"Temporary wallet private key: {temp_private_key}")
                self.stdout.write(f"You need to:")
                self.stdout.write(f"1. Fund this temporary wallet with devnet SOL from https://solfaucet.com/")
                self.stdout.write(f"2. Then run this command again with the --from-private-key option")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Failed to create temporary wallet: {e}"))
                return
                
            # Instructions for the user
            self.stdout.write(f"\n=== INSTRUCTIONS ===")
            self.stdout.write(f"To add {amount} SOL to {address}:")
            self.stdout.write(f"1. Fund the temporary wallet with at least {amount + Decimal('0.1')} SOL from https://solfaucet.com/")
            self.stdout.write(f"2. Run the following command:")
            self.stdout.write(f"   python manage.py send_test_funds --to-address {address} --amount {amount} --from-private-key YOUR_TEMP_PRIVATE_KEY")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Critical error: {e}"))
            logger.exception("Critical error in add_test_funds")

        self.stdout.write(f"\n=== Command completed ===")