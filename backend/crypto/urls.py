from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CryptocurrencyViewSet, CryptoPriceViewSet, ExchangePairViewSet,
    UserWalletViewSet, ExchangeCalculatorAPIView, InvestmentPlanViewSet,
    UserInvestmentViewSet, CardDepositViewSet,
    UserBalancesView,
    ExchangeRatesView,
    FiatDepositView,
    ExchangeCurrencyView
)

router = DefaultRouter()
router.register(r'cryptocurrencies', CryptocurrencyViewSet, basename='cryptocurrency')
router.register(r'prices', CryptoPriceViewSet, basename='price')
router.register(r'pairs', ExchangePairViewSet, basename='pair')
router.register(r'wallets', UserWalletViewSet, basename='wallet')
router.register(r'investment-plans', InvestmentPlanViewSet, basename='investment-plan')
router.register(r'investments', UserInvestmentViewSet, basename='investment')
router.register(r'card-deposits', CardDepositViewSet, basename='card-deposit')

urlpatterns = [
    path('', include(router.urls)),
    path('calculator/', ExchangeCalculatorAPIView.as_view(), name='calculator'),
    path('balances/', UserBalancesView.as_view(), name='user-balances'),
    path('exchange-rates/', ExchangeRatesView.as_view(), name='exchange-rates'),
    path('deposit-fiat/', FiatDepositView.as_view(), name='deposit-fiat'),
    path('exchange-currency/', ExchangeCurrencyView.as_view(), name='exchange-currency'),
]