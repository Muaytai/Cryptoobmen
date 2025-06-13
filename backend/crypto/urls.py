from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserWalletViewSet, ExchangeCalculatorAPIView, InvestmentPlanViewSet,
    UserInvestmentViewSet, UserBalancesView,
    ExchangeRatesView, ExchangeRateView, LatestCryptoPricesView
)
from .views_deposit import DepositInfoView, DepositStatusView

router = DefaultRouter()
router.register(r'user-wallets', UserWalletViewSet, basename='user-wallet')
router.register(r'investment-plans', InvestmentPlanViewSet, basename='investment-plan')
router.register(r'user-investments', UserInvestmentViewSet, basename='user-investment')

urlpatterns = [
    path('', include(router.urls)),
    path('exchange-calculator/', ExchangeCalculatorAPIView.as_view(), name='exchange-calculator'),
    path('user-balances/', UserBalancesView.as_view(), name='user-balances'),
    path('exchange-rates/', ExchangeRatesView.as_view(), name='exchange-rates'),
    path('exchange-rate/', ExchangeRateView.as_view(), name='exchange-rate'),
    path('latest-crypto-prices/', LatestCryptoPricesView.as_view(), name='latest-crypto-prices'),
    path('deposit/info/', DepositInfoView.as_view(), name='deposit-info'),
    path('deposit/status/<str:memo>/', DepositStatusView.as_view(), name='deposit-status'),
]