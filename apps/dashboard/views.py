from django.db.models import Count, Sum, Avg, Max
from django.utils import timezone
from django.db.models.functions import TruncDate
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.accounts.permissions import IsAdmin
from apps.hiring.models import HiringRequest
from apps.payments.models import Transaction
from apps.accounts.models import User
from .models import (
    AnalyticsEvent,
    DailyStatistics,
    UserActivity,
    SystemConfiguration
)
from .serializers import (
    AnalyticsEventSerializer,
    DailyStatisticsSerializer,
    UserActivitySerializer,
    SystemConfigurationSerializer,
    UserDashboardActivitySerializer
)
from apps.hiring.serializers import HiringRequestListSerializer, HiringRequestDetailSerializer
import logging

logger = logging.getLogger(__name__)

class UserDashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get user dashboard data"""
        try:
            user = request.user

            # Get user's hiring requests stats
            total_requests = HiringRequest.objects.filter(user=user).count()
            active_requests = HiringRequest.objects.filter(
                user=user,
                status__in=['pending', 'in_progress']
            ).count()
            completed_requests = HiringRequest.objects.filter(
                user=user,
                status='completed'
            ).count()
            total_spent = HiringRequest.objects.filter(
                user=user,
                status__in=['paid', 'completed']
            ).aggregate(
                total=Sum('quoted_price')
            )['total'] or 0

            # Get recent activities (hiring requests)
            recent_activities = HiringRequest.objects.filter(
                user=user
            ).order_by('-created_at')[:5]

            return Response({
                'stats': {
                    'total_requests': total_requests,
                    'active_requests': active_requests,
                    'completed_requests': completed_requests,
                    'total_spent': total_spent
                },
                'recent_activities': UserDashboardActivitySerializer(
                    recent_activities, many=True
                ).data
            })
        except Exception as e:
            logger.error(f"Error getting user dashboard data: {str(e)}")
            return Response(
                {'error': 'Failed to get dashboard data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AdminDashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAdmin]
    
    def get_request_object(self, pk):
        try:
            return HiringRequest.objects.get(pk=pk)
        except HiringRequest.DoesNotExist:
            return None

    @action(detail=False, methods=['get'])
    def admin_stats(self, request):
        """Get admin dashboard statistics"""
        try:
            # Get basic stats
            total_requests = HiringRequest.objects.count()
            pending_requests = HiringRequest.objects.filter(status='pending').count()
            completed_requests = HiringRequest.objects.filter(status='completed').count()
            total_revenue = HiringRequest.objects.filter(
                status__in=['paid', 'completed']
            ).aggregate(
                total=Sum('quoted_price')
            )['total'] or 0

            # Get recent requests
            recent_requests = HiringRequest.objects.select_related(
                'user', 'service_type'
            ).order_by('-created_at')[:5]

            # Get requests by status
            requests_by_status = (
                HiringRequest.objects.values('status')
                .annotate(count=Count('id'))
                .order_by('status')
            )

            # Get requests by service
            requests_by_service = (
                HiringRequest.objects.values(
                    'service_type__name'
                ).annotate(
                    count=Count('id')
                ).order_by('-count')
            )

            return Response({
                'total_requests': total_requests,
                'pending_requests': pending_requests,
                'completed_requests': completed_requests,
                'total_revenue': total_revenue,
                'recent_requests': HiringRequestListSerializer(
                    recent_requests, many=True
                ).data,
                'requests_by_status': requests_by_status,
                'requests_by_service': [
                    {'service': item['service_type__name'], 'count': item['count']}
                    for item in requests_by_service
                ]
            })
        except Exception as e:
            logger.error(f"Error getting admin stats: {str(e)}")
            return Response(
                {'error': 'Failed to get admin statistics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def requests(self, request):
        """Get all hiring requests with filters"""
        queryset = HiringRequest.objects.all().select_related('user', 'service_type')
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        service_type = request.query_params.get('service_type')
        if service_type:
            queryset = queryset.filter(service_type=service_type)
            
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)
            
        # Order by most recent first
        queryset = queryset.order_by('-created_at')
        
        serializer = HiringRequestListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def request_detail(self, request, pk=None):
        """Get details of a specific hiring request"""
        hiring_request = self.get_request_object(pk)
        if not hiring_request:
            return Response(
                {'error': 'Hiring request not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = HiringRequestDetailSerializer(hiring_request)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def update_request(self, request, pk=None):
        """Update a hiring request"""
        hiring_request = self.get_request_object(pk)
        if not hiring_request:
            return Response(
                {'error': 'Hiring request not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = HiringRequestDetailSerializer(
            hiring_request, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def set_price(self, request, pk=None):
        """Set price for a hiring request"""
        hiring_request = self.get_request_object(pk)
        if not hiring_request:
            return Response(
                {'error': 'Hiring request not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        price = request.data.get('price')
        if price is None:
            return Response(
                {'error': 'Price is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        hiring_request.quoted_price = price
        hiring_request.save()
        
        serializer = HiringRequestDetailSerializer(hiring_request)
        return Response(serializer.data)

class AnalyticsEventViewSet(viewsets.ModelViewSet):
    serializer_class = AnalyticsEventSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        queryset = AnalyticsEvent.objects.all()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(created_at__range=[start_date, end_date])
        
        # Filter by event type
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        return queryset

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary of events grouped by type"""
        summary = (
            AnalyticsEvent.objects.values('event_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        return Response(summary)

class DailyStatisticsViewSet(viewsets.ModelViewSet):
    queryset = DailyStatistics.objects.all()
    serializer_class = DailyStatisticsSerializer
    permission_classes = [IsAdmin]

    @action(detail=False, methods=['post'])
    def generate_daily_stats(self, request):
        """Generate statistics for a specific date or today"""
        try:
            date = request.data.get('date', timezone.now().date())
            stats = DailyStatistics.objects.create_or_update_stats(date)
            serializer = self.get_serializer(stats)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error generating daily stats: {str(e)}")
            return Response(
                {'error': 'Failed to generate statistics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get trends over time"""
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timezone.timedelta(days=days)
        
        stats = DailyStatistics.objects.filter(
            date__range=[start_date, end_date]
        ).order_by('date')
        
        serializer = self.get_serializer(stats, many=True)
        return Response(serializer.data)

class UserActivityViewSet(viewsets.ModelViewSet):
    serializer_class = UserActivitySerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        queryset = UserActivity.objects.all()
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        # Filter by activity type
        activity_type = self.request.query_params.get('activity_type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
            
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(created_at__range=[start_date, end_date])
            
        return queryset.order_by('-created_at')

    @action(detail=False, methods=['get'])
    def user_summary(self, request):
        """Get summary of activities by user"""
        summary = (
            UserActivity.objects.values('user__username')
            .annotate(
                total_activities=Count('id'),
                last_activity=Max('created_at')
            )
            .order_by('-total_activities')
        )
        return Response(summary)

class SystemConfigurationViewSet(viewsets.ModelViewSet):
    queryset = SystemConfiguration.objects.all()
    serializer_class = SystemConfigurationSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_public=True)
        return queryset

    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Update multiple configuration settings at once"""
        try:
            configs = request.data.get('configs', [])
            updated = []
            
            for config in configs:
                instance = SystemConfiguration.objects.get(id=config['id'])
                serializer = self.get_serializer(
                    instance,
                    data=config,
                    partial=True
                )
                if serializer.is_valid():
                    serializer.save()
                    updated.append(serializer.data)
                    
            return Response(updated)
        except SystemConfiguration.DoesNotExist:
            return Response(
                {'error': 'One or more configurations not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error in bulk update: {str(e)}")
            return Response(
                {'error': 'Failed to update configurations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class HiringRequestViewSet(viewsets.ModelViewSet):
    serializer_class = HiringRequestListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return HiringRequest.objects.all().order_by('-created_at')
        return HiringRequest.objects.filter(user=user).order_by('-created_at')

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary of requests grouped by status"""
        user = request.user
        queryset = self.get_queryset()
        
        summary = (
            queryset
            .values('status')
            .annotate(
                count=Count('id'),
                latest=Max('created_at')
            )
            .order_by('-count')
        )
        return Response(summary)
