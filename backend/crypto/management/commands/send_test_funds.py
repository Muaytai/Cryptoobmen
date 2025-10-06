from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, UserWallet
from crypto.blockchain.factory import get_blockchain_service
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sends test funds from one wallet to another'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to-address',
            type=str,
            required=True,
            help='Destination address',
        )
        parser.add_argument(
            '--amount',
            type=str,
            default='1.0',
            help='Amount to send (default: 1.0 SOL)',
        )
        parser.add_argument(
            '--from-private-key',
            type=str,
            required=True,
            help='Private key of the sender wallet',
        )
        parser.add_argument(
            '--network',
            type=str,
            default='devnet',
            help='Solana network (default: devnet)',
        )

    def handle(self, *args, **options):
        to_address = options['to_address']
        amount = Decimal(options['amount'])
        from_private_key = options['from_private_key']
        network = options['network']
        
        self.stdout.write(f"=== Sending test funds ===")
        self.stdout.write(f"To: {to_address}")
        self.stdout.write(f"Amount: {amount} SOL")
        self.stdout.write(f"Network: {network}")
        
        try:
            # Get the Solana service
            try:
                service = get_blockchain_service('solana')
                self.stdout.write(self.style.SUCCESS(f"✓ Initialized Solana service"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Failed to initialize Solana service: {e}"))
                return

            # Validate destination address
            if not service.validate_address(to_address):
                self.stdout.write(self.style.ERROR(f"✗ Invalid destination address: {to_address}"))
                return
            self.stdout.write(self.style.SUCCESS("✓ Destination address is valid"))

            # Get sender address from private key
            try:
                key_bytes = service._parse_private_key(from_private_key)
                from solders.keypair import Keypair
                keypair = Keypair.from_bytes(key_bytes)
                sender_address = str(keypair.pubkey())
                self.stdout.write(self.style.SUCCESS(f"✓ Sender address: {sender_address}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Failed to parse private key: {e}"))
                return

            # Check sender balance
            try:
                sender_balance = service.get_balance(sender_address)
                self.stdout.write(f"Sender balance: {sender_balance} SOL")
                
                min_needed = amount + Decimal('0.01')  # Reserve for fees
                if sender_balance < min_needed:
                    self.stdout.write(self.style.ERROR(
                        f"✗ Insufficient funds! Need: {min_needed} SOL, available: {sender_balance} SOL"
                    ))
                    return
                    
                self.stdout.write(self.style.SUCCESS("✓ Sufficient funds available"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Failed to check sender balance: {e}"))
                return

            # Send the transaction
            self.stdout.write(f"\n--- Sending transaction ---")
            try:
                tx_hash = service.send_transaction(
                    from_private_key,
                    to_address,
                    amount,
                    f"test_funds_addition"
                )
                
                self.stdout.write(self.style.SUCCESS(f"✓ Transaction sent successfully!"))
                self.stdout.write(f"  Hash: {tx_hash}")
                self.stdout.write(f"  Explorer: https://explorer.solana.com/tx/{tx_hash}?cluster=devnet")
                
                # Update database if this is a system wallet
                try:
                    sol_currency = Cryptocurrency.objects.get(symbol__iexact='SOL')
                    target_wallet = UserWallet.objects.get(
                        deposit_address=to_address,
                        currency=sol_currency
                    )
                    target_wallet.balance += amount
                    target_wallet.available_balance += amount
                    target_wallet.save()
                    self.stdout.write(self.style.SUCCESS(f"✓ Updated wallet balance in database"))
                    self.stdout.write(f"  New balance: {target_wallet.balance} SOL")
                except UserWallet.DoesNotExist:
                    self.stdout.write(self.style.WARNING("⚠ Wallet not found in database, skipping balance update"))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"⚠ Failed to update database: {e}"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Failed to send transaction: {e}"))
                logger.exception("Transaction error")
                return

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Critical error: {e}"))
            logger.exception("Critical error in send_test_funds")

        self.stdout.write(f"\n=== Command completed ===")