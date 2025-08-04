from django.core.management.base import BaseCommand, CommandError
from transactions.models import Transaction, Withdrawal
from crypto.tasks import process_withdrawal
import uuid

class Command(BaseCommand):
    help = 'Finds a specific withdrawal by its transaction UUID and re-queues it for processing.'

    def add_arguments(self, parser):
        parser.add_argument('transaction_id', type=str, help='The UUID of the transaction to reprocess.')

    def handle(self, *args, **options):
        transaction_id_str = options['transaction_id']
        
        try:
            transaction_uuid = uuid.UUID(transaction_id_str)
        except ValueError:
            raise CommandError(f'Invalid UUID format: "{transaction_id_str}"')

        self.stdout.write(f"Searching for transaction with ID: {transaction_uuid}")

        try:
            transaction = Transaction.objects.get(transaction_id=transaction_uuid)
        except Transaction.DoesNotExist:
            raise CommandError(f'Transaction with ID {transaction_uuid} not found.')

        if transaction.type != 'withdrawal':
            raise CommandError(f'Transaction {transaction_uuid} is not a withdrawal (type: {transaction.type}).')

        try:
            withdrawal = Withdrawal.objects.get(transaction=transaction)
        except Withdrawal.DoesNotExist:
            # This case might happen if the withdrawal record was deleted but the transaction remained.
            raise CommandError(f'Withdrawal record associated with transaction {transaction_uuid} not found.')

        self.stdout.write(self.style.SUCCESS(f"Found Withdrawal ID: {withdrawal.id} associated with Transaction ID: {transaction.transaction_id}"))
        self.stdout.write(f"Current status: {transaction.status}")

        if transaction.status not in ['pending', 'failed']:
            self.stdout.write(self.style.WARNING(f"Withdrawal is not in a 'pending' or 'failed' state. Its current status is '{transaction.status}'. Reprocessing may not be necessary or could have unintended side effects."))
            confirm = input("Do you want to proceed anyway? (yes/no): ")
            if confirm.lower() != 'yes':
                self.stdout.write("Reprocessing cancelled by user.")
                return

        # Re-queue the withdrawal processing task to a high-priority queue
        process_withdrawal.apply_async(args=[withdrawal.id], queue='high_priority')

        # Optionally, you might want to reset the status to 'pending' if it was 'failed'
        if transaction.status == 'failed':
            transaction.status = 'pending'
            transaction.notes = 'Manually re-queued for processing by admin command.'
            transaction.save()
            self.stdout.write(self.style.SUCCESS(f"Reset status to 'pending' and re-queued withdrawal {withdrawal.id} to 'high_priority' queue."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully re-queued withdrawal {withdrawal.id} to 'high_priority' queue."))
