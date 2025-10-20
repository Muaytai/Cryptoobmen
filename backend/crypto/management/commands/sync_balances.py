from django.core.management.base import BaseCommand
from crypto.tasks import sync_balances_with_blockchain

class Command(BaseCommand):
    help = "Синхронизирует балансы в базе данных с реальными балансами в блокчейне"

    def add_arguments(self, parser):
        parser.add_argument(
            '--async',
            action='store_true',
            help='Запустить синхронизацию асинхронно через Celery',
        )

    def handle(self, *args, **options):
        if options['async']:
            self.stdout.write("Запуск синхронизации балансов через Celery...")
            task = sync_balances_with_blockchain.delay()
            self.stdout.write(self.style.SUCCESS(f"Задача запущена с ID: {task.id}"))
        else:
            self.stdout.write("Запуск синхронизации балансов синхронно...")
            result = sync_balances_with_blockchain()
            self.stdout.write(self.style.SUCCESS(f"Результат: {result}"))
