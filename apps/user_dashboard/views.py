from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from apps.hiring.models import HiringRequest
from apps.payments.models import Transaction
from .models import (
    UserDashboardPreference,
    UserNotification,
    UserDocument,
    UserStats
)
from .serializers import (
    UserDashboardPreferenceSerializer,
    UserNotificationSerializer,
    UserDocumentSerializer,
    UserStatsSerializer,
    DashboardHiringRequestSerializer,
    DashboardTransactionSerializer,
    DashboardOverviewSerializer
)

class UserDashboardPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = UserDashboardPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserDashboardPreference.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserNotificationViewSet(viewsets.ModelViewSet):
    serializer_class = UserNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserNotification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response(status=status.HTTP_200_OK)

class UserDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = UserDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserDocument.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        document = self.get_object()
        document.is_archived = True
        document.save()
        return Response(status=status.HTTP_200_OK)

class DashboardOverviewViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        # Get user stats
        stats, _ = UserStats.objects.get_or_create(user=request.user)

        # Get recent requests
        recent_requests = HiringRequest.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]

        # Get recent transactions
        recent_transactions = Transaction.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]

        # Get unread notifications
        unread_notifications = UserNotification.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')[:5]

        # Prepare data for serialization
        data = {
            'stats': stats,
            'recent_requests': recent_requests,
            'recent_transactions': recent_transactions,
            'unread_notifications': unread_notifications
        }

        serializer = DashboardOverviewSerializer(data)
        return Response(serializer.data)

class UserRequestViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DashboardHiringRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = HiringRequest.objects.filter(user=self.request.user)
        
        # Filter by status
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)

        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date and end_date:
            queryset = queryset.filter(created_at__range=[start_date, end_date])

        return queryset.order_by('-created_at')

class UserTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DashboardTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Transaction.objects.filter(user=self.request.user)
        
        # Filter by status
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)

        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date and end_date:
            queryset = queryset.filter(created_at__range=[start_date, end_date])

        return queryset.order_by('-created_at')
