from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CryptocurrencyViewSet, CryptoPriceViewSet, ExchangePairViewSet,
    UserWalletViewSet, ExchangeCalculatorAPIView, InvestmentPlanViewSet,
    UserInvestmentViewSet, CardDepositViewSet
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
]