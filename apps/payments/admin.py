from django.contrib import admin
from .models import (
    PaymentMethod,
    Transaction,
    Receipt,
    Refund,
    PaymentWebhook
)

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'payment_type', 'is_active')
    list_filter = ('payment_type', 'is_active')
    search_fields = ('name', 'description')
    ordering = ('name',)

class ReceiptInline(admin.StackedInline):
    model = Receipt
    can_delete = False
    readonly_fields = ('generated_at',)
    extra = 0

class RefundInline(admin.TabularInline):
    model = Refund
    readonly_fields = ('created_at', 'updated_at')
    extra = 0

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'reference_id', 'user', 'hiring_request',
        'amount', 'currency', 'status', 'created_at'
    )
    list_filter = ('status', 'currency', 'payment_method')
    search_fields = (
        'reference_id', 'user__username',
        'hiring_request__title'
    )
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ReceiptInline, RefundInline]
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'user', 'hiring_request', 'payment_method',
                'reference_id'
            )
        }),
        ('Payment Details', {
            'fields': ('amount', 'currency', 'status')
        }),
        ('Additional Data', {
            'fields': ('payment_data',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = (
        'transaction', 'amount', 'status',
        'refunded_at', 'created_at'
    )
    list_filter = ('status',)
    search_fields = (
        'transaction__reference_id',
        'transaction__user__username'
    )
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('transaction', 'amount', 'reason')
        }),
        ('Status', {
            'fields': ('status', 'refunded_at')
        }),
        ('Additional Data', {
            'fields': ('refund_data',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )

@admin.register(PaymentWebhook)
class PaymentWebhookAdmin(admin.ModelAdmin):
    list_display = (
        'event_type', 'processed',
        'created_at'
    )
    list_filter = ('event_type', 'processed')
    search_fields = ('event_type', 'error_message')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Webhook Information', {
            'fields': ('event_type', 'payload')
        }),
        ('Processing Status', {
            'fields': ('processed', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        })
    )
