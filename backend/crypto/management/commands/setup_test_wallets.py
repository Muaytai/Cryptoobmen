from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings

from crypto.models import Cryptocurrency, SystemWalletAddress


class Command(BaseCommand):
    """Создаёт/обновляет SystemWalletAddress для всех криптовалют,
    устанавливая единый тестовый адрес (из переменной окружения или константы).
    Запуск:
        python manage.py setup_test_wallets --address TMGXLnRtHjzdS9b4Ddoes95s6mmLvT9yrh
    Если аргумент не указан, берётся settings.TEST_SYSTEM_ADDRESS.
    """

    help = "Создать одинаковые системные кошельки для всех криптовалют на время теста."

    def add_arguments(self, parser):
        parser.add_argument(
            "--address",
            type=str,
            help="Адрес, который будет установлен во всех SystemWalletAddress",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        address = (
            options.get("address")
            or getattr(settings, "TEST_SYSTEM_ADDRESS", None)
            or "TMGXLnRtHjzdS9b4Ddoes95s6mmLvT9yrh"
        )

        self.stdout.write(self.style.WARNING(f"Используется адрес: {address}"))

        cryptos = Cryptocurrency.objects.filter(currency_type="crypto")
        created, updated = 0, 0

        for crypto in cryptos:
            obj, was_created = SystemWalletAddress.objects.update_or_create(
                currency=crypto,
                network=crypto.network,
                defaults={"address": address},
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово. Создано: {created}, обновлено: {updated} системных адресов."
            )
        )
