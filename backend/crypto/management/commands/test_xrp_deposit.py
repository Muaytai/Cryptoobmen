from __future__ import annotations

import time
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from crypto.services_deposit import DepositService
from crypto.models import SystemWalletAddress, UserDepositMemo, Cryptocurrency
from crypto.blockchain.xrp import XRPL_NETWORKS
from crypto.tasks import check_blockchain_deposits

from xrpl.clients import JsonRpcClient
from xrpl.wallet import generate_faucet_wallet
from xrpl.transaction import autofill_and_sign, submit_and_wait
from xrpl.models.transactions import Payment
from xrpl.utils import xrp_to_drops


class Command(BaseCommand):
    help = (
        "Создает тестовый депозит XRP на системный кошелек через XRPL faucet.\n"
        "Команда получает memo для пользователя (или использует заданный) и отправляет указанную сумму "
        "с тестового кошелька на системный адрес. После отправки можно автоматически запустить сканер депозитов."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-email",
            required=True,
            help="Email пользователя, для которого нужно получить memo.",
        )
        parser.add_argument(
            "--amount",
            type=str,
            default="1",
            help="Сумма XRP для отправки (по умолчанию 1 XRP).",
        )
        parser.add_argument(
            "--memo",
            help="Использовать конкретный memo/Destination Tag. Если не передан — будет создан новый.",
        )
        parser.add_argument(
            "--network",
            choices=list(XRPL_NETWORKS.keys()),
            default="testnet",
            help="XRPL сеть для отправки транзакции (по умолчанию testnet).",
        )
        parser.add_argument(
            "--run-scan",
            action="store_true",
            help="После отправки транзакции автоматически вызвать scan_deposits.",
        )
        parser.add_argument(
            "--wait-ledgers",
            type=int,
            default=2,
            help="Сколько новых ledger подождать после faucet-транзакции, прежде чем отправлять депозит (по умолчанию 2).",
        )

    def handle(self, *args, **options):
        user_email = options["user_email"]
        amount_raw = options["amount"]
        memo_override = options.get("memo")
        xrpl_network = options["network"]
        run_scan = options["run_scan"]
        wait_ledgers = options["wait_ledgers"]

        User = get_user_model()
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist as exc:
            raise CommandError(f"Пользователь с email '{user_email}' не найден.") from exc

        try:
            amount = Decimal(str(amount_raw))
        except Exception as exc:  # noqa: BLE001
            raise CommandError(f"Некорректное значение amount='{amount_raw}': {exc}") from exc

        if amount <= 0:
            raise CommandError("Сумма депозита должна быть больше нуля.")

        try:
            currency = Cryptocurrency.objects.get(symbol__iexact="XRP", network__iexact="XRP", is_active=True)
        except Cryptocurrency.DoesNotExist as exc:
            raise CommandError("Валюта XRP в системе не найдена или выключена.") from exc

        try:
            system_wallet = SystemWalletAddress.objects.get(currency=currency)
        except SystemWalletAddress.DoesNotExist as exc:
            raise CommandError("Не найден системный кошелек для XRP. Сначала запустите setup_xrp_system_address.") from exc

        memo_value = memo_override
        deposit_memo = None
        if memo_value:
            deposit_memo = UserDepositMemo.objects.filter(memo=memo_value, status="waiting", user=user).first()
            if not deposit_memo:
                raise CommandError(
                    f"Memo '{memo_value}' не найдено среди ожидающих для пользователя {user_email}. "
                    "Создайте новый memo или убедитесь, что он в статусе 'waiting'."
                )
            self.stdout.write(self.style.WARNING(f"Используется существующий memo {memo_value}."))
        else:
            # Создаем новый memo через сервис депозитов, чтобы соблюсти бизнес-логику
            address, memo_value, _, _ = DepositService.get_deposit_info(user, "XRP", "XRP")
            deposit_memo = UserDepositMemo.objects.get(memo=memo_value, status="waiting", user=user)
            self.stdout.write(self.style.SUCCESS(f"Создан новый memo {memo_value} для пользователя {user_email}."))
            if address != system_wallet.address:
                self.stdout.write(
                    self.style.WARNING(
                        f"Внимание: адрес из DepositService ({address}) отличается от системного кошелька ({system_wallet.address}). "
                        "Будет использован системный адрес."
                    )
                )

        client_url = XRPL_NETWORKS.get(xrpl_network)
        if not client_url:
            raise CommandError(f"Неизвестная XRPL сеть: {xrpl_network}")

        client = JsonRpcClient(client_url)
        self.stdout.write(self.style.NOTICE(f"XRPL клиент: {client_url}"))

        self.stdout.write("Запрос faucet и создание временного кошелька...")
        faucet_wallet = generate_faucet_wallet(client, debug=True)

        # Небольшая задержка, чтобы faucet-транзакция попала в ledger
        if wait_ledgers > 0:
            self.stdout.write(f"Ожидание {wait_ledgers} ledger перед отправкой депозита...")
            time.sleep(wait_ledgers * 4)  # ~4 сек на ledger в testnet

        drops_amount = xrp_to_drops(amount)
        payment = Payment(
            account=faucet_wallet.classic_address,
            destination=system_wallet.address,
            amount=str(drops_amount),
            destination_tag=int(memo_value),
        )

        self.stdout.write(
            f"Отправка {amount} XRP (drops={drops_amount}) "
            f"с {faucet_wallet.classic_address} на {system_wallet.address} с memo {memo_value}..."
        )

        signed_tx = autofill_and_sign(payment, client, faucet_wallet)
        response = submit_and_wait(signed_tx, client)

        if not response.is_successful():
            raise CommandError(f"Транзакция не была принята XRPL: {response}")

        tx_hash = response.result.get("hash")
        self.stdout.write(self.style.SUCCESS(f"Тестовая транзакция отправлена. Hash: {tx_hash}"))

        if run_scan:
            self.stdout.write("Запуск scan_deposits для немедленной обработки...")
            result = check_blockchain_deposits()
            self.stdout.write(self.style.SUCCESS(f"scan_deposits завершился: {result}"))

        self.stdout.write(
            self.style.SUCCESS(
                "Готово. Проверьте Django Admin или лог scan_deposits, чтобы убедиться в обработке депозита."
            )
        )

