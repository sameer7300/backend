from rest_framework import serializers
from apps.hiring.models import HiringRequest
from apps.payments.models import Transaction
from .models import (
    UserDashboardPreference,
    UserNotification,
    UserDocument,
    UserStats
)

class UserDashboardPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDashboardPreference
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

class UserNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotification
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

class UserDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDocument
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

class UserStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStats
        fields = '__all__'
        read_only_fields = ['user', 'last_updated']

class DashboardHiringRequestSerializer(serializers.ModelSerializer):
    service_type_name = serializers.CharField(source='service_type.name')
    status_display = serializers.CharField(source='get_status_display')
    
    class Meta:
        model = HiringRequest
        fields = [
            'id', 'title', 'service_type_name', 'status',
            'status_display', 'priority', 'deadline',
            'quoted_price', 'created_at'
        ]

class DashboardTransactionSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display')
    payment_method_name = serializers.CharField(source='payment_method.name')
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'reference_id', 'amount', 'currency',
            'status', 'status_display', 'payment_method_name',
            'created_at'
        ]

class DashboardOverviewSerializer(serializers.Serializer):
    stats = UserStatsSerializer()
    recent_requests = DashboardHiringRequestSerializer(many=True)
    recent_transactions = DashboardTransactionSerializer(many=True)
    unread_notifications = UserNotificationSerializer(many=True)
