from django.core.management.base import BaseCommand, CommandError
from crypto.models import SystemWalletAddress

class Command(BaseCommand):
    help = 'Deletes a SystemWalletAddress object with a specific malformed address.'

    def handle(self, *args, **options):
        malformed_address = 'TEST_XRP_XRP_4JFZT8XRRQ'
        
        try:
            wallet_to_delete = SystemWalletAddress.objects.get(address=malformed_address)
            wallet_to_delete.delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted wallet with address: {malformed_address}'))
        except SystemWalletAddress.DoesNotExist:
            self.stdout.write(self.style.WARNING(f'Wallet with address {malformed_address} not found.'))
        except Exception as e:
            raise CommandError(f'An error occurred: {e}')
