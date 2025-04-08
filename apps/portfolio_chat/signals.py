from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import Message, Notification
from .utils import send_message_notification

@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    if created:
        conversation = instance.conversation
        for participant in conversation.participants.exclude(id=instance.sender.id):
            # Create in-app notification
            Notification.objects.create(
                recipient=participant,
                type='message',
                title=f'New message from {instance.sender.username}',
                content=instance.content[:100] + '...' if len(instance.content) > 100 else instance.content,
                related_conversation=conversation,
                related_message=instance
            )

            # Send email notification if enabled
            if hasattr(participant, 'profile') and participant.profile.email_notifications_enabled:
                try:
                    # Create message preview
                    message_preview = instance.content[:200] + '...' if len(instance.content) > 200 else instance.content
                    
                    # Use the utility function to send the notification
                    send_message_notification(
                        recipient_email=participant.email,
                        sender_name=instance.sender.username,
                        message_preview=message_preview
                    )
                except Exception as e:
                    print(f"Failed to send email to {participant.email}: {str(e)}")
