from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    AnalyticsEvent,
    DailyStatistics,
    UserActivity,
    SystemConfiguration
)

@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'event_name', 'user_link', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['event_name', 'user__username', 'user__email']
    readonly_fields = ['created_at']
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:accounts_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return '-'
    user_link.short_description = 'User'

@admin.register(DailyStatistics)
class DailyStatisticsAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'total_users', 'active_users', 'new_users',
        'total_requests', 'completed_requests', 'total_revenue',
        'average_request_value'
    ]
    list_filter = ['date']
    date_hierarchy = 'date'
    readonly_fields = ['date']

    def has_add_permission(self, request):
        # Statistics should only be generated through the API
        return False

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = [
        'user_link', 'activity_type', 'ip_address',
        'created_at', 'truncated_description'
    ]
    list_filter = ['activity_type', 'created_at']
    search_fields = [
        'user__username', 'user__email',
        'description', 'ip_address'
    ]
    readonly_fields = ['created_at']

    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'

    def truncated_description(self, obj):
        return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
    truncated_description.short_description = 'Description'

@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ['key', 'is_public', 'updated_at', 'truncated_description']
    list_filter = ['is_public', 'updated_at']
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['key']

    def truncated_description(self, obj):
        return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
    truncated_description.short_description = 'Description'
