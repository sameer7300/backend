from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AnalyticsEventViewSet,
    DailyStatisticsViewSet,
    UserActivityViewSet,
    SystemConfigurationViewSet,
    AdminDashboardViewSet,
    UserDashboardViewSet
)

router = DefaultRouter()
router.register(r'analytics', AnalyticsEventViewSet, basename='analytics')
router.register(r'stats', DailyStatisticsViewSet)
router.register(r'activities', UserActivityViewSet, basename='activities')
router.register(r'config', SystemConfigurationViewSet)
router.register(r'admin', AdminDashboardViewSet, basename='admin-dashboard')
router.register(r'user', UserDashboardViewSet, basename='user-dashboard')

app_name = 'dashboard'

urlpatterns = [
    path('', include(router.urls)),
]
