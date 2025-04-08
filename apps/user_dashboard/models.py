from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class UserDashboardPreference(models.Model):
    """User preferences for dashboard customization"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboard_preferences'
    )
    default_view = models.CharField(
        max_length=50,
        choices=[
            ('overview', _('Overview')),
            ('requests', _('Requests')),
            ('transactions', _('Transactions')),
            ('messages', _('Messages')),
        ],
        default='overview'
    )
    notification_email = models.BooleanField(default=True)
    notification_web = models.BooleanField(default=True)
    items_per_page = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email}'s Dashboard Preferences"

class UserNotification(models.Model):
    """User notifications for various events"""
    class Category(models.TextChoices):
        REQUEST = 'request', _('Request Update')
        PAYMENT = 'payment', _('Payment Update')
        MESSAGE = 'message', _('New Message')
        SYSTEM = 'system', _('System Update')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboard_notifications'
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.email}"

class UserDocument(models.Model):
    """User document management"""
    class DocumentType(models.TextChoices):
        RECEIPT = 'receipt', _('Receipt')
        INVOICE = 'invoice', _('Invoice')
        CONTRACT = 'contract', _('Contract')
        ATTACHMENT = 'attachment', _('Attachment')
        OTHER = 'other', _('Other')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboard_documents'
    )
    title = models.CharField(max_length=200)
    document_type = models.CharField(
        max_length=20,
        choices=DocumentType.choices
    )
    file = models.FileField(upload_to='user_documents/')
    description = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_document_type_display()}"

class UserStats(models.Model):
    """User activity statistics"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboard_stats'
    )
    total_requests = models.IntegerField(default=0)
    active_requests = models.IntegerField(default=0)
    completed_requests = models.IntegerField(default=0)
    total_spent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    last_activity = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Stats for {self.user.email}"
