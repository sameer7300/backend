from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentMethodViewSet,
    TransactionViewSet,
    RefundViewSet,
    PaymentWebhookViewSet
)

app_name = 'payments'

router = DefaultRouter()
router.register(r'methods', PaymentMethodViewSet)
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'refunds', RefundViewSet, basename='refund')
router.register(r'webhooks', PaymentWebhookViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
