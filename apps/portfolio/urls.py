from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectViewSet,
    SkillViewSet,
    TimelineViewSet,
    ResumeViewSet,
    ContactViewSet,
)

app_name = 'portfolio'

router = DefaultRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'skills', SkillViewSet)
router.register(r'timeline', TimelineViewSet)
router.register(r'resume', ResumeViewSet)
router.register(r'contacts', ContactViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
