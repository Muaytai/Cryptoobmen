"""
Management command для исправления некорректных адресов Polygon кошельков
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from crypto.models import UserWallet
from crypto.blockchain.factory import get_blockchain_service


class Command(BaseCommand):
    help = 'Fix invalid Polygon wallet addresses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even valid addresses',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write(
            self.style.SUCCESS('🔍 Analyzing Polygon wallets...')
        )

        # Находим все Polygon кошельки
        polygon_wallets = UserWallet.objects.filter(
            currency__symbol='POL',
            currency__network='Polygon'
        ).select_related('currency', 'user')

        if not polygon_wallets.exists():
            self.stdout.write(
                self.style.WARNING('No Polygon wallets found.')
            )
            return

        # Анализируем каждый кошелек
        valid_count = 0
        invalid_count = 0
        system_count = 0
        
        wallets_to_fix = []

        for wallet in polygon_wallets:
            addr = wallet.deposit_address
            user_email = wallet.user.email if wallet.user else 'System'
            
            if wallet.is_system_wallet:
                system_count += 1
                status = 'SYSTEM'
            elif addr is None:
                invalid_count += 1
                status = 'NULL'
                wallets_to_fix.append(wallet)
            elif not addr.startswith('0x') or len(addr) != 42:
                invalid_count += 1
                status = 'INVALID'
                wallets_to_fix.append(wallet)
            else:
                valid_count += 1
                status = 'VALID'
                if force:
                    wallets_to_fix.append(wallet)
            
            self.stdout.write(
                f'ID: {wallet.id}, User: {user_email}, Status: {status}, Address: {addr}'
            )

        # Статистика
        self.stdout.write('')
        self.stdout.write(f'📊 Statistics:')
        self.stdout.write(f'  Valid: {valid_count}')
        self.stdout.write(f'  Invalid: {invalid_count}')
        self.stdout.write(f'  System: {system_count}')
        self.stdout.write(f'  Total: {polygon_wallets.count()}')

        if not wallets_to_fix:
            self.stdout.write(
                self.style.SUCCESS('✅ All wallets have valid addresses!')
            )
            return

        self.stdout.write('')
        self.stdout.write(f'🔧 Wallets to fix: {len(wallets_to_fix)}')

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN - No changes will be made')
            )
            return

        # Исправляем кошельки
        try:
            service = get_blockchain_service('polygon')
            
            with transaction.atomic():
                fixed_count = 0
                
                for wallet in wallets_to_fix:
                    try:
                        old_address = wallet.deposit_address
                        new_address, private_key = service.create_new_address(user_id=wallet.user.id)
                        
                        wallet.deposit_address = new_address
                        wallet.encrypted_private_key = private_key
                        wallet.save(update_fields=['deposit_address', 'encrypted_private_key'])
                        
                        fixed_count += 1
                        user_email = wallet.user.email if wallet.user else 'System'
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✅ Fixed wallet ID {wallet.id} ({user_email}): '
                                f'{old_address} -> {new_address}'
                            )
                        )
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'❌ Error fixing wallet ID {wallet.id}: {e}'
                            )
                        )

                self.stdout.write('')
                self.stdout.write(
                    self.style.SUCCESS(f'🎉 Successfully fixed {fixed_count} wallets!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Critical error: {e}')
            )
