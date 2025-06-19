from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CryptocurrencyViewSet, UserWalletViewSet, ExchangeCalculatorAPIView, 
    ExchangeRatesView, ExchangeRateView, LatestCryptoPricesView, ExchangePairViewSet,
    perform_exchange_view, ExchangeOrderViewSet
)
from .views_deposit import DepositInfoView, DepositStatusView

router = DefaultRouter()
router.register(r'cryptocurrencies', CryptocurrencyViewSet, basename='cryptocurrency')
router.register(r'wallets', UserWalletViewSet, basename='user-wallet')
router.register(r'exchange-pairs', ExchangePairViewSet, basename='exchange-pair')
router.register(r'exchange-orders', ExchangeOrderViewSet, basename='exchange-order')

urlpatterns = [
    path('', include(router.urls)),
    path('wallets/balance/', UserWalletViewSet.as_view({'get': 'balance'}), name='user-wallet-balance'),
    path('exchange/calculator/', ExchangeCalculatorAPIView.as_view(), name='exchange-calculator'),
    path('exchange/execute/', perform_exchange_view, name='perform-exchange'),
    path('exchange-rates/', ExchangeRatesView.as_view(), name='exchange-rates'),
    path('exchange-rate/', ExchangeRateView.as_view(), name='exchange-rate'),
    path('prices/latest/', LatestCryptoPricesView.as_view(), name='latest-crypto-prices'),
    path('deposit/info/', DepositInfoView.as_view(), name='deposit-info'),
    path('deposit/status/<str:memo>/', DepositStatusView.as_view(), name='deposit-status'),
]