from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, UserWallet
from crypto.blockchain.factory import get_blockchain_service
from decimal import Decimal
import logging
from django.db import transaction

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix system-wide cryptocurrency issues and missing system wallets'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix-system-wallets',
            action='store_true',
            help='Create missing system wallets for all active cryptocurrencies',
        )
        parser.add_argument(
            '--check-networks',
            action='store_true',
            help='Check and fix network configurations',
        )
        parser.add_argument(
            '--fix-all',
            action='store_true',
            help='Run all fixes',
        )

    def handle(self, *args, **options):
        self.stdout.write("=== System-wide Cryptocurrency Issues Fix ===\n")
        
        if options.get('fix_all'):
            options['fix_system_wallets'] = True
            options['check_networks'] = True
        
        if options.get('check_networks', True):
            self.fix_network_configurations()
        
        if options.get('fix_system_wallets', True):
            self.create_missing_system_wallets()
        
        self.stdout.write(self.style.SUCCESS("\n✅ All fixes completed!"))

    def fix_network_configurations(self):
        """Fix network configurations for all cryptocurrencies"""
        self.stdout.write("\n--- FIXING NETWORK CONFIGURATIONS ---")
        
        # Network mappings for proper configuration
        network_fixes = {
            'BNB': 'BEP20',  # Keep as BEP20 but handle in factory
            'BTC': 'BTC',
            'ETH': 'ERC20',
            'LTC': 'LTC',
            'MATIC': 'POLYGON',
            'XRP': 'XRP',
            'SOL': 'solana',  # Already fixed
            'USDT': 'TRC20',  # Default to TRC20
        }
        
        for symbol, correct_network in network_fixes.items():
            try:
                currencies = Cryptocurrency.objects.filter(symbol__iexact=symbol, is_active=True)
                for currency in currencies:
                    if currency.network != correct_network:
                        old_network = currency.network
                        currency.network = correct_network
                        currency.save()
                        self.stdout.write(f"✓ Fixed {symbol} network: {old_network} -> {correct_network}")
                    else:
                        self.stdout.write(f"✓ {symbol} network already correct: {correct_network}")
            except Exception as e:
                self.stdout.write(f"⚠ Error fixing {symbol}: {e}")

    def create_missing_system_wallets(self):
        """Create missing system wallets for all active cryptocurrencies"""
        self.stdout.write("\n--- CREATING MISSING SYSTEM WALLETS ---")
        
        active_currencies = Cryptocurrency.objects.filter(is_active=True)
        created_count = 0
        skipped_count = 0
        
        for currency in active_currencies:
            try:
                # Check if system wallet already exists
                system_wallet, created = UserWallet.objects.get_or_create(
                    currency=currency,
                    is_system_wallet=True,
                    defaults={
                        'user': None,
                        'balance': Decimal('0'),
                        'is_active': True,
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f"✓ Created system wallet for {currency.symbol} ({currency.network})")
                    
                    # Try to generate address for supported networks
                    try:
                        if currency.network in ['solana', 'BTC', 'TRC20', 'ERC20']:
                            service = get_blockchain_service(currency.network)
                            address, private_key = service.create_new_address()
                            system_wallet.deposit_address = address
                            system_wallet.encrypted_private_key = private_key
                            system_wallet.save()
                            self.stdout.write(f"  └─ Generated address: {address}")
                    except Exception as addr_e:
                        self.stdout.write(f"  └─ ⚠ Could not generate address: {addr_e}")
                        
                else:
                    skipped_count += 1
                    self.stdout.write(f"⊕ System wallet for {currency.symbol} already exists")
                    
            except Exception as e:
                self.stdout.write(f"✗ Failed to create system wallet for {currency.symbol}: {e}")
        
        self.stdout.write(f"\n📊 Results:")
        self.stdout.write(f"  Created: {created_count} system wallets")
        self.stdout.write(f"  Skipped: {skipped_count} existing wallets")

    def check_blockchain_services(self):
        """Check which blockchain services are working"""
        self.stdout.write("\n--- CHECKING BLOCKCHAIN SERVICES ---")
        
        services_to_test = [
            ('solana', 'Solana'),
            ('BTC', 'Bitcoin'),
            ('TRC20', 'Tron'),
            ('ERC20', 'Ethereum'),
            ('XRP', 'Ripple'),
        ]
        
        for network, name in services_to_test:
            try:
                service = get_blockchain_service(network)
                self.stdout.write(f"✓ {name} service: OK")
            except Exception as e:
                self.stdout.write(f"✗ {name} service: {e}")