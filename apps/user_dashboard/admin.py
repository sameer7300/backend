from django.contrib import admin
from .models import (
    UserDashboardPreference,
    UserNotification,
    UserDocument,
    UserStats
)

@admin.register(UserDashboardPreference)
class UserDashboardPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'default_view', 'notification_email', 'notification_web', 'created_at']
    list_filter = ['default_view', 'notification_email', 'notification_web']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'title', 'is_read', 'created_at']
    list_filter = ['category', 'is_read', 'created_at']
    search_fields = ['user__email', 'user__username', 'title', 'message']
    readonly_fields = ['created_at']

@admin.register(UserDocument)
class UserDocumentAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'document_type', 'is_archived', 'created_at']
    list_filter = ['document_type', 'is_archived', 'created_at']
    search_fields = ['user__email', 'user__username', 'title', 'description']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(UserStats)
class UserStatsAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'total_requests', 'active_requests',
        'completed_requests', 'total_spent', 'last_activity'
    ]
    readonly_fields = ['last_updated']
    search_fields = ['user__email', 'user__username']
