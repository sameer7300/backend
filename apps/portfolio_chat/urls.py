from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConversationViewSet, MessageViewSet, NotificationViewSet, UserListView, AIChatView

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('users/', UserListView.as_view(), name='user-list'),
    path('ai-chat/', AIChatView.as_view(), name='ai-chat'),
]
