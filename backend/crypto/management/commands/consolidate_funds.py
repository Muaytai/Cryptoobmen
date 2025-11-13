"""
Команда для ручного запуска задачи консолидации средств.
"""
from django.core.management.base import BaseCommand
from crypto.tasks import consolidate_funds

class Command(BaseCommand):
    help = "Запускает задачу консолидации средств с депозитных адресов на системные."

    def handle(self, *args, **options):
        self.stdout.write("Запуск задачи consolidate_funds...")
        # Запускаем задачу синхронно для немедленного выполнения
        consolidate_funds.apply()
        self.stdout.write(self.style.SUCCESS("Задача consolidate_funds завершена."))