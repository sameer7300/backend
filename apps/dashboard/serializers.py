from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import (
    AnalyticsEvent,
    DailyStatistics,
    UserActivity,
    SystemConfiguration
)
from apps.hiring.models import HiringRequest

class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ['app_label', 'model']

class AnalyticsEventSerializer(serializers.ModelSerializer):
    content_type = ContentTypeSerializer(read_only=True)
    user = serializers.SerializerMethodField()

    class Meta:
        model = AnalyticsEvent
        fields = [
            'id', 'event_type', 'event_name', 'user',
            'content_type', 'object_id', 'data', 'created_at'
        ]

    def get_user(self, obj):
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'email': obj.user.email
            }
        return None

class DailyStatisticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyStatistics
        fields = [
            'date', 'total_users', 'active_users', 'new_users',
            'total_requests', 'completed_requests', 'total_revenue',
            'average_request_value'
        ]

class UserActivitySerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = UserActivity
        fields = [
            'id', 'user', 'activity_type', 'description',
            'ip_address', 'user_agent', 'created_at'
        ]

    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email
        }

class SystemConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfiguration
        fields = [
            'id', 'key', 'value', 'description',
            'is_public', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'value': {'write_only': True}  # Only admins can see the actual values
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # Only include value if user is admin or config is public
        if not instance.is_public and (not request or not request.user.is_staff):
            data.pop('value', None)
        
        return data

class UserDashboardActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = HiringRequest
        fields = [
            'id', 'title', 'status', 'description',
            'quoted_price', 'created_at'
        ]
