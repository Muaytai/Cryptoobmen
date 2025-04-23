from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CryptocurrencyViewSet, CryptoPriceViewSet, ExchangePairViewSet,
    UserWalletViewSet, ExchangeCalculatorAPIView
)

router = DefaultRouter()
router.register(r'cryptocurrencies', CryptocurrencyViewSet, basename='cryptocurrency')
router.register(r'prices', CryptoPriceViewSet, basename='price')
router.register(r'pairs', ExchangePairViewSet, basename='pair')
router.register(r'wallets', UserWalletViewSet, basename='wallet')

urlpatterns = [
    path('', include(router.urls)),
    path('calculator/', ExchangeCalculatorAPIView.as_view(), name='calculator'),
] 