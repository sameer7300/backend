from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.conf import settings

class AnalyticsEvent(models.Model):
    """
    Track various events in the system for analytics purposes
    """
    class EventType(models.TextChoices):
        PAGE_VIEW = 'page_view', _('Page View')
        USER_ACTION = 'user_action', _('User Action')
        SYSTEM_EVENT = 'system_event', _('System Event')
        ERROR = 'error', _('Error')

    event_type = models.CharField(max_length=20, choices=EventType.choices)
    event_name = models.CharField(max_length=100)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analytics_events'
    )
    # Generic foreign key to associate event with any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    data = models.JSONField(default=dict, help_text='Additional event data')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

class DailyStatistics(models.Model):
    """
    Daily aggregated statistics for quick dashboard display
    """
    date = models.DateField(unique=True)
    total_users = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0)
    new_users = models.PositiveIntegerField(default=0)
    total_requests = models.PositiveIntegerField(default=0)
    completed_requests = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    average_request_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"Stats for {self.date}"

class UserActivity(models.Model):
    """
    Detailed user activity tracking
    """
    class ActivityType(models.TextChoices):
        LOGIN = 'login', _('Login')
        LOGOUT = 'logout', _('Logout')
        PROFILE_UPDATE = 'profile_update', _('Profile Update')
        PASSWORD_CHANGE = 'password_change', _('Password Change')
        REQUEST_CREATE = 'request_create', _('Request Create')
        PAYMENT = 'payment', _('Payment')
        OTHER = 'other', _('Other')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboard_activities'
    )
    activity_type = models.CharField(max_length=20, choices=ActivityType.choices)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'activity_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()}"

class SystemConfiguration(models.Model):
    """
    System-wide configuration settings
    """
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField()
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False, help_text='Whether this config is visible to non-admin users')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['key']

    def __str__(self):
        return self.key
