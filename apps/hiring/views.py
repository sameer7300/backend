from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string
import logging
from decimal import Decimal, DecimalException
from django.utils import timezone
import random
import string

from .models import (
    ServiceType,
    PriceModifier,
    HiringRequest,
    RequestAttachment,
    RequestMessage,
    RequestStatusHistory
)
from .serializers import (
    ServiceTypeSerializer,
    PriceModifierSerializer,
    HiringRequestListSerializer,
    HiringRequestDetailSerializer,
    HiringRequestCreateSerializer,
    HiringRequestUpdateSerializer,
    RequestAttachmentSerializer,
    RequestMessageSerializer
)
from apps.accounts.permissions import IsAdmin

logger = logging.getLogger(__name__)

class ServiceTypeViewSet(viewsets.ModelViewSet):
    queryset = ServiceType.objects.all()
    serializer_class = ServiceTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_staff:
            return ServiceType.objects.all()
        return ServiceType.objects.filter(is_active=True)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdmin]
        return super().get_permissions()

class PriceModifierViewSet(viewsets.ModelViewSet):
    queryset = PriceModifier.objects.all()
    serializer_class = PriceModifierSerializer
    permission_classes = [IsAdmin]

class HiringRequestViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return HiringRequest.objects.none()
            
        if user.is_staff:
            return HiringRequest.objects.all().select_related('user', 'service_type')
            
        return HiringRequest.objects.filter(user=user).select_related('user', 'service_type')

    def get_serializer_class(self):
        if self.action == 'create':
            return HiringRequestCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return HiringRequestUpdateSerializer
        elif self.action == 'list':
            return HiringRequestListSerializer
        return HiringRequestDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Set the user to the current authenticated user
        hiring_request = serializer.save(user=request.user)
        
        # Create initial status history
        RequestStatusHistory.objects.create(
            request=hiring_request,
            old_status='',
            new_status='pending',
            changed_by=request.user
        )

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_update(self, serializer):
        instance = serializer.save()
        
        # If status changed, create status history
        if 'status' in serializer.validated_data:
            old_status = instance.status
            new_status = serializer.validated_data['status']
            if old_status != new_status:
                RequestStatusHistory.objects.create(
                    request=instance,
                    old_status=old_status,
                    new_status=new_status,
                    changed_by=self.request.user
                )

    def get_object(self):
        obj = super().get_object()
        # Check if user has permission to access this object
        if not self.request.user.is_staff and obj.user != self.request.user:
            raise permissions.exceptions.PermissionDenied(
                "You do not have permission to access this request."
            )
        return obj

    def submit(self, request, pk=None):
        logger.info(f"Received request to submit hiring request: {pk}")
        
        try:
            hiring_request = self.get_object()
            if hiring_request.status != 'draft':
                logger.error(f"Hiring request is not in draft status: {hiring_request.status}")
                return Response(
                    {'error': 'Only draft requests can be submitted'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            hiring_request.status = 'submitted'
            hiring_request.save()
            logger.info(f"Submitted hiring request: {hiring_request.id}")

            # Create status history
            RequestStatusHistory.objects.create(
                request=hiring_request,
                old_status='draft',
                new_status='submitted',
                changed_by=request.user
            )

            # Notify admin
            if hasattr(settings, 'ADMIN_EMAIL'):
                send_mail(
                    'New Hiring Request Submitted',
                    f'A new hiring request "{hiring_request.title}" has been submitted by {request.user.username}.',
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL],
                    fail_silently=True,
                )

            serializer = HiringRequestDetailSerializer(
                hiring_request,
                context={'request': request}
            )
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def add_message(self, request, pk=None):
        logger.info(f"Received request to add message to hiring request: {pk}")
        
        try:
            hiring_request = self.get_object()
            message = request.data.get('message')
            is_internal = request.data.get('is_internal', False)

            if not message:
                logger.error(f"No message provided")
                return Response(
                    {'error': 'Message is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Only staff can create internal messages
            if is_internal and not request.user.is_staff:
                logger.error(f"User is not staff and cannot create internal messages")
                return Response(
                    {'error': 'You cannot create internal messages'},
                    status=status.HTTP_403_FORBIDDEN
                )

            message = RequestMessage.objects.create(
                request=hiring_request,
                sender=request.user,
                message=message,
                is_internal=is_internal
            )
            logger.info(f"Added message to hiring request: {message.id}")

            serializer = RequestMessageSerializer(message)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def upload_attachment(self, request, pk=None):
        logger.info(f"Received request to upload attachment to hiring request: {pk}")
        
        try:
            hiring_request = self.get_object()
            files = request.FILES.getlist('files')
            description = request.data.get('description', '')

            if not files:
                logger.error(f"No files provided")
                return Response(
                    {'error': 'No files provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            attachments = []
            for file in files:
                attachment = RequestAttachment.objects.create(
                    request=hiring_request,
                    file=file,
                    description=description
                )
                attachments.append(attachment)
                logger.info(f"Uploaded attachment to hiring request: {attachment.id}")

            serializer = RequestAttachmentSerializer(attachments, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def apply_price_modifiers(self, request, pk=None):
        logger.info(f"Received request to apply price modifiers to hiring request: {pk}")
        
        try:
            if not request.user.is_staff:
                logger.error(f"User is not staff and cannot apply price modifiers")
                return Response(
                    {'error': 'Only staff can apply price modifiers'},
                    status=status.HTTP_403_FORBIDDEN
                )

            hiring_request = self.get_object()
            modifier_ids = request.data.get('modifiers', [])
            
            # Clear existing modifiers
            hiring_request.applied_modifiers.clear()
            
            # Add new modifiers
            modifiers = PriceModifier.objects.filter(id__in=modifier_ids, is_active=True)
            hiring_request.applied_modifiers.add(*modifiers)

            # Calculate new price based on modifiers
            base_price = hiring_request.service_type.base_price
            final_price = base_price

            for modifier in modifiers:
                if modifier.modifier_type == 'multiplier':
                    final_price *= modifier.value
                elif modifier.modifier_type == 'fixed':
                    final_price += modifier.value
                elif modifier.modifier_type == 'percentage':
                    final_price += (base_price * (modifier.value / 100))

            hiring_request.quoted_price = final_price
            hiring_request.save()
            logger.info(f"Applied price modifiers to hiring request: {hiring_request.id}")

            serializer = HiringRequestDetailSerializer(
                hiring_request,
                context={'request': request}
            )
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['GET'])
    def messages(self, request, pk=None):
        """Get messages for a hiring request"""
        try:
            hiring_request = self.get_object()
            messages = RequestMessage.objects.filter(request=hiring_request)
            serializer = RequestMessageSerializer(messages, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting messages: {str(e)}")
            return Response(
                {'error': 'Failed to get messages'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['POST'])
    def add_message(self, request, pk=None):
        """Add a message to a hiring request"""
        try:
            hiring_request = self.get_object()
            message_text = request.data.get('message', '').strip()
            
            if not message_text:
                return Response(
                    {'error': 'Message text is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            message = RequestMessage.objects.create(
                request=hiring_request,
                sender=request.user,
                message=message_text
            )
            
            serializer = RequestMessageSerializer(message)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")
            return Response(
                {'error': 'Failed to add message'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['POST'])
    def set_price(self, request, pk=None):
        """Set price for a hiring request"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff members can set prices'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            hiring_request = self.get_object()
            price = request.data.get('price')
            
            if not price:
                return Response(
                    {'error': 'Price is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                price = Decimal(price)
                if price <= 0:
                    raise ValueError('Price must be positive')
            except (ValueError, DecimalException) as e:
                return Response(
                    {'error': 'Invalid price value'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            hiring_request.price = price
            hiring_request.status = 'priced'
            hiring_request.save()
            
            # Create status history
            RequestStatusHistory.objects.create(
                request=hiring_request,
                old_status='pending',
                new_status='priced',
                changed_by=request.user,
                notes=f'Price set to ${price}'
            )
            
            serializer = HiringRequestDetailSerializer(hiring_request)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error setting price: {str(e)}")
            return Response(
                {'error': 'Failed to set price'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['POST'])
    def process_payment(self, request, pk=None):
        """Process payment for a hiring request"""
        try:
            hiring_request = self.get_object()
            
            if hiring_request.status != 'priced':
                return Response(
                    {'error': 'Request must be priced before payment'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not hiring_request.price:
                return Response(
                    {'error': 'Price not set for this request'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # TODO: Integrate with actual payment gateway
            # For now, just mark as paid
            hiring_request.status = 'paid'
            hiring_request.save()
            
            # Create status history
            RequestStatusHistory.objects.create(
                request=hiring_request,
                old_status='priced',
                new_status='paid',
                changed_by=request.user,
                notes=f'Payment processed for ${hiring_request.price}'
            )
            
            serializer = HiringRequestDetailSerializer(hiring_request)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}")
            return Response(
                {'error': 'Failed to process payment'},
                status=status.HTTP_400_BAD_REQUEST
            )
