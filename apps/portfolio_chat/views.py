from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q
from django.utils import timezone
from .models import Conversation, Message, Notification, AIChatMessage
from .serializers import ConversationSerializer, MessageSerializer, NotificationSerializer, AIChatMessageSerializer
from django.conf import settings
from django.http import FileResponse
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from .utils import send_message_notification, get_ai_response, generate_session_id
import logging
from rest_framework import serializers

class UserListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        User = get_user_model()
        users = User.objects.exclude(id=request.user.id)
        return Response([{
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        } for user in users])

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user)

    def perform_create(self, serializer):
        conversation = serializer.save()
        conversation.participants.add(self.request.user)
        participant_id = self.request.data.get('participant_id')
        if participant_id:
            conversation.participants.add(participant_id)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        conversation = self.get_object()
        if not conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {"error": "You are not a participant in this conversation"},
                status=status.HTTP_403_FORBIDDEN
            )
        messages = conversation.messages.order_by('created_at')  # Order by oldest first
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        conversation = self.get_object()
        
        # Create a mutable copy of request.data
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        
        # Add conversation ID to the data
        data['conversation'] = conversation.id
        
        serializer = MessageSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            message = serializer.save(
                sender=request.user,
                conversation=conversation
            )
            
            # Send email notification to other participants
            for participant in conversation.participants.all():
                if participant != request.user:
                    try:
                        # Create message preview
                        message_preview = message.content[:200] + '...' if len(message.content) > 200 else message.content
                        if message.file:
                            message_preview = f"File: {message.file_name}\n{message_preview}"
                        
                        # Send notification using Django's email system
                        from .utils import send_message_notification
                        
                        # Handle admin users with empty names
                        if request.user.is_staff:
                            sender_display_name = "Admin"
                        else:
                            sender_display_name = request.user.get_full_name() or request.user.username or request.user.email
                        
                        success = send_message_notification(
                            recipient_email=participant.email,
                            sender_name=sender_display_name,
                            message_preview=message_preview
                        )
                        if success:
                            logging.info(f"Email notification sent to {participant.email}")
                        else:
                            logging.warning(f"Failed to send email notification to {participant.email}")
                    except Exception as e:
                        logging.error(f"Failed to send email to {participant.email}: {str(e)}")

            return Response(MessageSerializer(message, context={'request': request}).data)
        else:
            # Log the validation errors for debugging
            logging.error(f"Message validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def available_users(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        users = User.objects.exclude(id=request.user.id)
        return Response([{
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        } for user in users])

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs.get('conversation_pk')
        return Message.objects.filter(conversation_id=conversation_id)

    def perform_create(self, serializer):
        conversation_id = self.kwargs.get('conversation_pk')
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            
            # Ensure the user is a participant in the conversation
            if not conversation.participants.filter(id=self.request.user.id).exists():
                raise serializers.ValidationError({"error": "You are not a participant in this conversation"})
                
            message = serializer.save(
                sender=self.request.user,
                conversation=conversation
            )
            
            # Send email notification to other participants
            for participant in conversation.participants.all():
                if participant != self.request.user:
                    try:
                        # Create message preview
                        message_preview = message.content[:100] + '...' if len(message.content) > 100 else message.content
                        if message.file:
                            message_preview = f"File: {message.file_name}" + (f" - {message_preview}" if message.content else "")
                        
                        # Send notification using Django's email system
                        from .utils import send_message_notification
                        
                        # Handle admin users with empty names
                        if self.request.user.is_staff:
                            sender_display_name = "Admin"
                        else:
                            sender_display_name = self.request.user.get_full_name() or self.request.user.username or self.request.user.email
                        
                        success = send_message_notification(
                            recipient_email=participant.email,
                            sender_name=sender_display_name,
                            message_preview=message_preview
                        )
                        
                        if success:
                            logging.info(f"Email notification sent to {participant.email}")
                        else:
                            logging.warning(f"Failed to send email notification to {participant.email}")
                    except Exception as e:
                        logging.error(f"Failed to send email to {participant.email}: {str(e)}")
            return message
        except Conversation.DoesNotExist:
            raise serializers.ValidationError({"error": f"Conversation with id {conversation_id} does not exist"})

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        message = self.get_object()
        message.mark_as_read()
        return Response(MessageSerializer(message, context={'request': request}).data)

    @action(detail=True, methods=['get'])
    def download_file(self, request, pk=None):
        message = self.get_object()
        if not message.file:
            return Response({'error': 'No file attached'}, status=400)
        
        file_path = message.file.path
        content_type = message.file_type or 'application/octet-stream'
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{message.file_name}"'
        return response

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        notifications = self.get_queryset().filter(is_read=False)
        notifications.update(is_read=True, read_at=timezone.now())
        return Response({"status": "success"})

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_as_read()
        return Response(NotificationSerializer(notification).data)

class AIChatView(APIView):
    permission_classes = [permissions.AllowAny]  # Allow anonymous users to chat with the AI
    
    def post(self, request):
        """
        Handle a new message to the AI chatbot
        """
        # Get the user message from the request
        user_message = request.data.get('message')
        session_id = request.data.get('session_id')
        
        # Validate input
        if not user_message:
            return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Generate a new session ID if not provided
        if not session_id:
            session_id = generate_session_id()
        
        # Get the authenticated user if available
        user = request.user if request.user.is_authenticated else None
        
        # Get response from AI
        response_data = get_ai_response(user_message, session_id, user)
        
        return Response(response_data)
    
    def get(self, request):
        """
        Get chat history for a session
        """
        session_id = request.query_params.get('session_id')
        
        if not session_id:
            return Response({'error': 'Session ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the authenticated user if available
        user = request.user if request.user.is_authenticated else None
        
        # Query for messages in this session
        if user and user.is_authenticated:
            # If authenticated, get messages for this user and session
            messages = AIChatMessage.objects.filter(session_id=session_id, user=user)
        else:
            # If anonymous, just get messages for this session
            messages = AIChatMessage.objects.filter(session_id=session_id, user=None)
        
        # Serialize and return the messages
        serializer = AIChatMessageSerializer(messages, many=True)
        
        return Response({
            'session_id': session_id,
            'messages': serializer.data
        })
