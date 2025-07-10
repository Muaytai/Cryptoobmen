"""Однократное сканирование блокчейна Ethereum для входящих депозитов.

Команда переиспользует бизнес-логику Celery-таска
`crypto.tasks.check_blockchain_deposits`, позволяя запускать её вручную
без поднятия воркера/beat. Удобно для локальной отладки на Windows.
"""
from django.core.management.base import BaseCommand

from crypto.tasks import check_blockchain_deposits


class Command(BaseCommand):
    help = "Проверяет ERC20-депозиты прямо сейчас (без Celery)."

    def handle(self, *args, **options):  # noqa: D401 – командная форма
        processed = check_blockchain_deposits()
        self.stdout.write(self.style.SUCCESS(f"Готово, обработано: {processed}")) 