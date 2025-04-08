from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from apps.hiring.models import HiringRequest

# Create your models here.

class PaymentMethod(models.Model):
    class PaymentType(models.TextChoices):
        SAFEPAY = 'safepay', _('SafePay')
        BANK_TRANSFER = 'bank_transfer', _('Bank Transfer')
        OTHER = 'other', _('Other')

    name = models.CharField(max_length=100)
    payment_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices,
        default=PaymentType.SAFEPAY
    )
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_payment_type_display()})"

class Transaction(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PROCESSING = 'processing', _('Processing')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
        REFUNDED = 'refunded', _('Refunded')
        CANCELLED = 'cancelled', _('Cancelled')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    hiring_request = models.ForeignKey(
        HiringRequest,
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, default='PKR')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    reference_id = models.CharField(
        max_length=100,
        unique=True,
        help_text='External payment reference ID'
    )
    payment_data = models.JSONField(
        default=dict,
        help_text='Additional payment-specific data'
    )
    # SafePay specific fields
    safepay_tracker = models.CharField(
        max_length=100,
        blank=True,
        help_text='SafePay payment tracker ID'
    )
    safepay_checkout_url = models.URLField(
        blank=True,
        help_text='SafePay checkout URL'
    )
    safepay_status = models.CharField(
        max_length=50,
        blank=True,
        help_text='SafePay payment status'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference_id} - {self.get_status_display()}"

class Receipt(models.Model):
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.PROTECT,
        related_name='receipt'
    )
    receipt_number = models.CharField(max_length=50, unique=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.receipt_number

class Refund(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PROCESSING = 'processing', _('Processing')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
        CANCELLED = 'cancelled', _('Cancelled')

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.PROTECT,
        related_name='refunds'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    refund_data = models.JSONField(
        default=dict,
        help_text='Additional refund-specific data'
    )
    refunded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Refund for {self.transaction.reference_id}"

class PaymentWebhook(models.Model):
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    processed = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type} at {self.created_at}"
