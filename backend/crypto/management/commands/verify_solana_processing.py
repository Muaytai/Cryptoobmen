from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, UserWallet
from crypto.blockchain.factory import get_blockchain_service
from accounts.models import User
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Verify Solana deposit processing functionality'

    def add_arguments(self, parser):
        parser.add_argument('--user-id', type=int, help='User ID to test with')
        parser.add_argument('--address', type=str, help='Specific address to test')

    def handle(self, *args, **options):
        self.stdout.write("=== Verifying Solana Deposit Processing ===\n")
        
        try:
            # 1. Check if SOL currency exists
            try:
                sol_currency = Cryptocurrency.objects.get(symbol='SOL')
                self.stdout.write(self.style.SUCCESS(f"✓ SOL currency found: {sol_currency.name} ({sol_currency.symbol})"))
                self.stdout.write(f"  Network: {sol_currency.network}")
                self.stdout.write(f"  Decimals: {sol_currency.decimals}")
                self.stdout.write(f"  Requires Memo: {sol_currency.requires_memo}")
            except Cryptocurrency.DoesNotExist:
                self.stdout.write(self.style.ERROR("✗ SOL currency not found"))
                return
                
            # 2. Check if system wallet exists
            try:
                system_wallet = UserWallet.objects.get(currency=sol_currency, is_system_wallet=True)
                self.stdout.write(self.style.SUCCESS(f"✓ System wallet found: {system_wallet.deposit_address}"))
                self.stdout.write(f"  Balance: {system_wallet.balance} SOL")
            except UserWallet.DoesNotExist:
                self.stdout.write(self.style.WARNING("⚠ System wallet not found (this is expected for address-based deposits)"))
                
            # 3. Test blockchain service
            try:
                service = get_blockchain_service(sol_currency.network)
                self.stdout.write(self.style.SUCCESS(f"✓ Blockchain service initialized: {service.__class__.__name__}"))
                self.stdout.write(f"  Network: {service.network}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Failed to initialize blockchain service: {e}"))
                return
                
            # 4. Test with specific address if provided
            if options['address']:
                self.stdout.write(f"\n--- Testing address: {options['address']} ---")
                
                # Test balance
                try:
                    balance = service.get_balance(options['address'])
                    self.stdout.write(self.style.SUCCESS(f"✓ Balance check successful: {balance} SOL"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ Balance check failed: {e}"))
                    
                # Test transactions
                try:
                    transactions = service.get_transactions(options['address'])
                    self.stdout.write(self.style.SUCCESS(f"✓ Transaction check successful: {len(transactions)} transactions found"))
                    for i, tx in enumerate(transactions[:3]):  # Show first 3 transactions
                        self.stdout.write(f"  Transaction {i+1}: {tx.get('value', 'N/A')} SOL from {tx.get('from_address', 'N/A')[:10]}...")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ Transaction check failed: {e}"))
                    
            # 5. Test with user wallet if user ID provided
            elif options['user_id']:
                self.stdout.write(f"\n--- Testing user ID: {options['user_id']} ---")
                
                try:
                    user = User.objects.get(id=options['user_id'])
                    self.stdout.write(self.style.SUCCESS(f"✓ User found: {user.email}"))
                    
                    # Get user's SOL wallet
                    try:
                        user_wallet = UserWallet.objects.get(user=user, currency=sol_currency)
                        self.stdout.write(self.style.SUCCESS(f"✓ User wallet found: {user_wallet.deposit_address}"))
                        
                        if user_wallet.deposit_address:
                            # Test balance
                            try:
                                balance = service.get_balance(user_wallet.deposit_address)
                                self.stdout.write(self.style.SUCCESS(f"✓ Wallet balance: {balance} SOL"))
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f"✗ Balance check failed: {e}"))
                                
                    except UserWallet.DoesNotExist:
                        self.stdout.write(self.style.WARNING("⚠ User wallet not found"))
                        
                except User.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"✗ User with ID {options['user_id']} not found"))
                    
            else:
                # 6. Create test address
                self.stdout.write("\n--- Creating test address ---")
                try:
                    test_address, test_private_key = service.create_new_address()
                    self.stdout.write(self.style.SUCCESS(f"✓ Test address created: {test_address}"))
                    
                    # Test balance
                    try:
                        balance = service.get_balance(test_address)
                        self.stdout.write(self.style.SUCCESS(f"✓ Test balance: {balance} SOL"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"✗ Test balance check failed: {e}"))
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ Failed to create test address: {e}"))
                    
            self.stdout.write(self.style.SUCCESS("\n=== Verification Complete ==="))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Critical error during verification: {e}"))
            logger.exception("Critical error during Solana verification")