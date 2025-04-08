from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ServiceTypeViewSet,
    PriceModifierViewSet,
    HiringRequestViewSet,
)

app_name = 'hiring'

router = DefaultRouter()
router.register(r'services', ServiceTypeViewSet)
router.register(r'modifiers', PriceModifierViewSet)
router.register(r'requests', HiringRequestViewSet, basename='request')

urlpatterns = [
    path('', include(router.urls)),
]
