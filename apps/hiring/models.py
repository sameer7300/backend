from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.utils import timezone
from nanoid import generate

class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

class PriceModifier(models.Model):
    class ModifierType(models.TextChoices):
        MULTIPLIER = 'multiplier', _('Multiplier')
        FIXED = 'fixed', _('Fixed Amount')
        PERCENTAGE = 'percentage', _('Percentage')

    name = models.CharField(max_length=100)
    description = models.TextField()
    modifier_type = models.CharField(
        max_length=20,
        choices=ModifierType.choices,
        default=ModifierType.PERCENTAGE
    )
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='For multiplier: 1.5 means 50% increase. For percentage: 15 means 15% increase.'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_modifier_type_display()})"

class HiringRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('priced', 'Priced'),
        ('paid', 'Paid'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    def generate_ticket_number(self):
        """Generate a unique ticket number with prefix HR-YYMM-XXXX"""
        prefix = 'HR'
        date_part = timezone.now().strftime('%y%m')
        unique_id = generate(size=8)  # Generate an 8-character unique ID
        return f'{prefix}-{date_part}-{unique_id}'

    ticket_number = models.CharField(
        max_length=20,  # Increased to accommodate the new format
        unique=True,
        editable=False,
        null=True,
        blank=True,
        db_index=True,  # Add index for faster lookups
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hiring_requests'
    )
    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.PROTECT,
        related_name='requests'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    quoted_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    admin_notes = models.TextField(blank=True)
    applied_modifiers = models.ManyToManyField(
        PriceModifier,
        related_name='requests',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('can_set_price', 'Can set price for request'),
            ('can_process_payment', 'Can process payment for request'),
        ]

    def __str__(self):
        return f"{self.ticket_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = self.generate_ticket_number()
        super().save(*args, **kwargs)

class RequestAttachment(models.Model):
    request = models.ForeignKey(
        HiringRequest,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='hiring/attachments/')
    description = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.request.title}"

class RequestMessage(models.Model):
    request = models.ForeignKey(
        HiringRequest,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_request_messages'
    )
    message = models.TextField()
    is_internal = models.BooleanField(
        default=False,
        help_text='If true, only admins can see this message'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.username} on {self.request.title}"

class RequestStatusHistory(models.Model):
    request = models.ForeignKey(
        HiringRequest,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    old_status = models.CharField(
        max_length=20,
        choices=HiringRequest.STATUS_CHOICES
    )
    new_status = models.CharField(
        max_length=20,
        choices=HiringRequest.STATUS_CHOICES
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='request_status_changes'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Request status histories'

    def __str__(self):
        return f"{self.request.title}: {self.old_status} → {self.new_status}"
