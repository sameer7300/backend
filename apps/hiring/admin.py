from django.contrib import admin
from .models import (
    ServiceType,
    PriceModifier,
    HiringRequest,
    RequestAttachment,
    RequestMessage,
    RequestStatusHistory
)

@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price', 'is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('order', 'name')

@admin.register(PriceModifier)
class PriceModifierAdmin(admin.ModelAdmin):
    list_display = ('name', 'modifier_type', 'value', 'is_active')
    list_filter = ('modifier_type', 'is_active')
    search_fields = ('name', 'description')

class RequestAttachmentInline(admin.TabularInline):
    model = RequestAttachment
    extra = 1

class RequestMessageInline(admin.TabularInline):
    model = RequestMessage
    extra = 0
    readonly_fields = ('sender', 'created_at')

class RequestStatusHistoryInline(admin.TabularInline):
    model = RequestStatusHistory
    extra = 0
    readonly_fields = ('old_status', 'new_status', 'changed_by', 'created_at')
    ordering = ('-created_at',)

@admin.register(HiringRequest)
class HiringRequestAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'user', 'service_type', 'status',
        'priority', 'deadline', 'created_at'
    )
    list_filter = ('status', 'priority', 'service_type')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [
        RequestAttachmentInline,
        RequestMessageInline,
        RequestStatusHistoryInline
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'user', 'service_type', 'title',
                'description', 'requirements'
            )
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority')
        }),
        ('Pricing', {
            'fields': (
                'budget', 'quoted_price', 'final_price',
                'applied_modifiers'
            )
        }),
        ('Dates', {
            'fields': ('deadline', 'created_at', 'updated_at')
        }),
        ('Notes', {
            'fields': ('admin_notes',)
        })
    )

@admin.register(RequestMessage)
class RequestMessageAdmin(admin.ModelAdmin):
    list_display = ('request', 'sender', 'is_internal', 'created_at')
    list_filter = ('is_internal', 'created_at')
    search_fields = ('message', 'sender__username', 'request__title')
    readonly_fields = ('created_at',)

@admin.register(RequestStatusHistory)
class RequestStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'request', 'old_status', 'new_status',
        'changed_by', 'created_at'
    )
    list_filter = ('old_status', 'new_status')
    search_fields = ('request__title', 'changed_by__username', 'notes')
    readonly_fields = ('created_at',)
