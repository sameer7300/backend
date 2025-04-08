from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserDashboardPreferenceViewSet,
    UserNotificationViewSet,
    UserDocumentViewSet,
    DashboardOverviewViewSet,
    UserRequestViewSet,
    UserTransactionViewSet
)

app_name = 'user_dashboard'

router = DefaultRouter()
router.register(r'preferences', UserDashboardPreferenceViewSet, basename='preference')
router.register(r'notifications', UserNotificationViewSet, basename='notification')
router.register(r'documents', UserDocumentViewSet, basename='document')
router.register(r'overview', DashboardOverviewViewSet, basename='overview')
router.register(r'requests', UserRequestViewSet, basename='request')
router.register(r'transactions', UserTransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
]
