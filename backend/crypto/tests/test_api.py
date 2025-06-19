from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from crypto.models import Cryptocurrency, UserWallet, Transfer, ExchangeOrder


class APITestEndpoints(APITestCase):
    """Тесты основных DRF эндпоинтов платформы кошелька."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="test", email="test@example.com", password="strong-pass-123")
        cls.other_user = User.objects.create_user(username="other", email="other@example.com", password="strong-pass-123")

        cls.btc = Cryptocurrency.objects.create(name="Bitcoin", symbol="BTC", is_active=True)
        cls.eth = Cryptocurrency.objects.create(name="Ethereum", symbol="ETH", is_active=True)

        # Кошельки пользователей
        cls.wallet1, _ = UserWallet.objects.get_or_create(
            user=cls.user, currency=cls.btc, is_system_wallet=False,
            defaults={"balance": Decimal("1.5"), "available_balance": Decimal("1.5")}
        )
        cls.wallet2, _ = UserWallet.objects.get_or_create(
            user=cls.user, currency=cls.eth, is_system_wallet=False,
            defaults={"balance": Decimal("10"), "available_balance": Decimal("10")}
        )
        UserWallet.objects.get_or_create(
            user=cls.other_user, currency=cls.btc, is_system_wallet=False,
            defaults={"balance": Decimal("3"), "available_balance": Decimal("3")}
        )

    def setUp(self):
        # Авторизуем основного пользователя для каждого запроса
        self.client.force_authenticate(user=self.user)

    # ---------- UserWallet ----------
    def test_user_wallet_list_returns_only_own(self):
        url = reverse("user-wallet-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        wallet_ids = {item["id"] for item in response.data}
        self.assertIn(self.wallet1.id, wallet_ids)
        self.assertIn(self.wallet2.id, wallet_ids)

    def test_user_wallet_balance_endpoint(self):
        url = reverse("user-wallet-balance")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("total_usd_balance", response.data)

    # ---------- Transfer ----------
    def test_transfer_list_returns_only_own(self):
        Transfer.objects.create(
            user=self.user, currency=self.btc, type="in", amount=Decimal("0.5"), status="completed"
        )
        Transfer.objects.create(
            user=self.other_user, currency=self.btc, type="out", amount=Decimal("1"), status="pending"
        )
        url = reverse("transfer-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(Decimal(response.data[0]["amount"]), Decimal("0.5"))

    # ---------- ExchangeOrder ----------
    def test_exchange_order_create(self):
        url = reverse("exchange-order-list")
        payload = {
            "from_currency_id": self.btc.id,
            "to_currency_id": self.eth.id,
            "from_amount": "0.1",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, 201)
        data = response.data
        self.assertEqual(data["from_currency"]["symbol"], "BTC")
        self.assertEqual(data["to_currency"]["symbol"], "ETH")
        order = ExchangeOrder.objects.get(id=data["id"])
        self.assertEqual(order.user, self.user)

