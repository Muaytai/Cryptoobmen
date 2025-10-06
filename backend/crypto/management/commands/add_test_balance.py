import logging
from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, UserWallet
from crypto.blockchain.factory import get_blockchain_service

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Add test balance directly to a wallet address'

    def add_arguments(self, parser):
        parser.add_argument('--address', type=str, required=True, help='Wallet address to add balance to')
        parser.add_argument('--amount', type=float, default=1.0, help='Amount to add (default: 1.0)')
        parser.add_argument('--network', type=str, default='devnet', help='Network to use (default: devnet)')

    def handle(self, *args, **options):
        address = options['address']
        amount = options['amount']
        network = options['network']
        
        self.stdout.write(f"=== Adding test balance directly to wallet ===")
        self.stdout.write(f"Address: {address}")
        self.stdout.write(f"Amount: {amount} SOL")
        self.stdout.write(f"Network: {network}")
        
        try:
            # Get the SOL currency with the specific network
            sol_currency = Cryptocurrency.objects.get(symbol__iexact='SOL', network=network)
            
            # Get the wallet
            try:
                wallet = UserWallet.objects.get(deposit_address=address, currency=sol_currency)
                self.stdout.write(f"Found wallet: {wallet.id}")
            except UserWallet.DoesNotExist:
                self.stdout.write("Wallet not found in database")
                return
            
            # Get blockchain service
            service = get_blockchain_service(network)
            
            # Add test funds
            tx_hash = service.add_test_funds(address, amount)
            
            if tx_hash:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully added {amount} SOL to {address}\n'
                        f'Transaction hash: {tx_hash}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR('Failed to add test funds')
                )
                
        except Cryptocurrency.DoesNotExist:
            self.stdout.write("SOL currency not found in database")
            return
        except Exception as e:
            logger.error(f"Error in add_test_balance", exc_info=True)
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
        
        self.stdout.write("=== Command completed ===")