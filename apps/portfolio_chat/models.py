from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import os

User = get_user_model()

def message_file_path(instance, filename):
    # Generate path: chat_files/user_<id>/<timestamp>_<filename>
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    return f'chat_files/user_{instance.sender.id}/{timestamp}_{filename}'

class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Conversation {self.id} between {', '.join([str(p) for p in self.participants.all()])}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    file = models.FileField(upload_to=message_file_path, null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    file_type = models.CharField(max_length=100, null=True, blank=True)
    file_size = models.IntegerField(null=True, blank=True)  # Size in bytes
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.file and not self.file_name:
            self.file_name = os.path.basename(self.file.name)
            self.file_type = os.path.splitext(self.file_name)[1].lower()
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    def __str__(self):
        return f"Message from {self.sender} in conversation {self.conversation.id}"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('message', 'New Message'),
        ('file', 'New File'),
        ('hiring', 'Hiring Update'),
        ('system', 'System Notification'),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    related_conversation = models.ForeignKey(Conversation, on_delete=models.SET_NULL, null=True, blank=True)
    related_message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, blank=True)
    extra_data = models.JSONField(null=True, blank=True)  # For storing additional context

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    def __str__(self):
        return f"{self.type} notification for {self.recipient}: {self.title}"

    class Meta:
        ordering = ['-created_at']

class AIChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_chat_messages', null=True, blank=True)
    session_id = models.CharField(max_length=100)  # To group messages from the same chat session
    role = models.CharField(max_length=20)  # 'user' or 'assistant'
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role} message at {self.created_at}"
