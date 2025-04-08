from django.contrib import admin
from .models import Conversation, Message, Notification

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'updated_at', 'is_active')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('participants__username', 'participants__email')
    filter_horizontal = ('participants',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('content', 'sender__username', 'sender__email')
    raw_id_fields = ('conversation', 'sender')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipient', 'type', 'title', 'created_at', 'is_read')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('title', 'content', 'recipient__username', 'recipient__email')
    raw_id_fields = ('recipient', 'related_conversation', 'related_message')
