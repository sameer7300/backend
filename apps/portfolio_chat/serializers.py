from rest_framework import serializers
from .models import Conversation, Message, Notification, AIChatMessage
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    is_admin = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_admin']
    
    def get_is_admin(self, obj):
        return obj.is_staff

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'content', 
            'file', 'file_name', 'file_type', 'file_size', 'file_url',
            'created_at', 'is_read', 'read_at'
        ]
        read_only_fields = ['created_at', 'is_read', 'read_at', 'file_name', 'file_type', 'file_size']

    def get_file_url(self, obj):
        if obj.file:
            return self.context['request'].build_absolute_uri(obj.file.url)
        return None

class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'created_at', 'updated_at', 'is_active', 'last_message', 'unread_count']
        read_only_fields = ['created_at', 'updated_at']

    def get_last_message(self, obj):
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return MessageSerializer(last_message, context=self.context).data
        return None

    def get_unread_count(self, obj):
        user = self.context['request'].user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'type', 'title', 'content', 'created_at', 
                 'is_read', 'read_at', 'related_conversation', 'related_message', 
                 'extra_data']
        read_only_fields = ['created_at', 'is_read', 'read_at']

class AIChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIChatMessage
        fields = ['id', 'user', 'session_id', 'role', 'content', 'created_at']
        read_only_fields = ['created_at']
