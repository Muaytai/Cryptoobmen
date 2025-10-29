from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TransactionViewSet, ExchangeViewSet, DepositViewSet, WithdrawalViewSet,
    ReviewViewSet, TransactionHistoryView, confirm_withdrawal_view
)

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'exchanges', ExchangeViewSet, basename='exchange')
router.register(r'deposits', DepositViewSet, basename='deposit')
router.register(r'withdrawals', WithdrawalViewSet, basename='withdrawal')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
    path('history/', TransactionHistoryView.as_view(), name='transaction-history'),
    path('withdrawals/confirm/<str:token>/', confirm_withdrawal_view, name='withdrawal-confirm'),
]
