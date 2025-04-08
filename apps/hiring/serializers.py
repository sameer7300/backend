from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    ServiceType,
    PriceModifier,
    HiringRequest,
    RequestAttachment,
    RequestMessage,
    RequestStatusHistory
)
from django.utils import timezone
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string

User = get_user_model()

class ServiceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceType
        fields = [
            'id', 'name', 'description', 'base_price',
            'is_active', 'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class PriceModifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceModifier
        fields = [
            'id', 'name', 'description', 'modifier_type',
            'value', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class RequestAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestAttachment
        fields = ['id', 'file', 'description', 'uploaded_at']
        read_only_fields = ['uploaded_at']

class RequestMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    
    class Meta:
        model = RequestMessage
        fields = [
            'id', 'sender', 'sender_name', 'message',
            'is_internal', 'created_at'
        ]
        read_only_fields = ['sender', 'created_at']

class RequestStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.username', read_only=True)
    old_status_display = serializers.CharField(source='get_old_status_display', read_only=True)
    new_status_display = serializers.CharField(source='get_new_status_display', read_only=True)

    class Meta:
        model = RequestStatusHistory
        fields = [
            'id', 'old_status', 'old_status_display',
            'new_status', 'new_status_display',
            'changed_by', 'changed_by_name',
            'notes', 'created_at'
        ]
        read_only_fields = ['created_at']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']

class HiringRequestSerializer(serializers.ModelSerializer):
    service_type = serializers.PrimaryKeyRelatedField(queryset=ServiceType.objects.all())
    email = serializers.EmailField(write_only=True, required=False)
    name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = HiringRequest
        fields = [
            'id',
            'service_type',
            'title',
            'description',
            'requirements',
            'priority',
            'deadline',
            'status',
            'quoted_price',
            'final_price',
            'created_at',
            'updated_at',
            'email',
            'name',
        ]
        read_only_fields = [
            'id',
            'status',
            'quoted_price',
            'final_price',
            'created_at',
            'updated_at',
        ]
        extra_kwargs = {
            'requirements': {'required': False, 'allow_blank': True},
            'deadline': {'required': False},
            'priority': {'default': 'medium'},
        }

class HiringRequestDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed hiring request view"""
    service_type = ServiceTypeSerializer()
    user = UserSerializer()
    applied_modifiers = PriceModifierSerializer(many=True)
    status_history = RequestStatusHistorySerializer(many=True, read_only=True)
    messages = RequestMessageSerializer(many=True, read_only=True)
    attachments = RequestAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = HiringRequest
        fields = [
            'id',
            'ticket_number',
            'user',
            'service_type',
            'title',
            'description',
            'requirements',
            'priority',
            'deadline',
            'status',
            'quoted_price',
            'final_price',
            'admin_notes',
            'applied_modifiers',
            'created_at',
            'updated_at',
            'status_history',
            'messages',
            'attachments',
        ]

class HiringRequestListSerializer(serializers.ModelSerializer):
    service_type_name = serializers.CharField(source='service_type.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = HiringRequest
        fields = [
            'id', 'title', 'service_type', 'service_type_name',
            'status', 'status_display', 'priority',
            'priority_display', 'deadline', 'created_at'
        ]
        read_only_fields = ['created_at']

class HiringRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new hiring request"""
    name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    
    class Meta:
        model = HiringRequest
        fields = [
            'service_type',
            'title',
            'description',
            'requirements',
            'priority',
            'deadline',
            'name',
            'email',
        ]
        
    def validate(self, data):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            if not data.get('name'):
                raise serializers.ValidationError({'name': 'Name is required for anonymous requests'})
            if not data.get('email'):
                raise serializers.ValidationError({'email': 'Email is required for anonymous requests'})
        return data

    def validate_service_type(self, value):
        if not value.is_active:
            raise serializers.ValidationError('This service is not currently available.')
        return value

    def validate_deadline(self, value):
        if value and value < timezone.now().date():
            raise serializers.ValidationError('Deadline cannot be in the past.')
        return value

    def create(self, validated_data):
        name = validated_data.pop('name', None)
        email = validated_data.pop('email', None)
        request = self.context.get('request')

        if not request.user.is_authenticated:
            # Create or get user for anonymous request
            User = get_user_model()
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=name.split()[0] if name else '',
                    last_name=' '.join(name.split()[1:]) if name and len(name.split()) > 1 else '',
                    password=get_random_string(12)
                )
            validated_data['user'] = user
        else:
            validated_data['user'] = request.user

        return super().create(validated_data)

class HiringRequestUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HiringRequest
        fields = [
            'title', 'description', 'requirements',
            'deadline', 'status', 'priority',
            'quoted_price', 'final_price', 'admin_notes'
        ]

    def validate_status(self, value):
        valid_transitions = {
            'pending': ['priced', 'cancelled'],
            'priced': ['paid', 'cancelled'],
            'paid': ['in_progress', 'cancelled'],
            'in_progress': ['completed', 'cancelled'],
            'completed': [],
            'cancelled': []
        }

        if not self.instance:
            return value

        current_status = self.instance.status
        if value != current_status and value not in valid_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f'Cannot transition from {current_status} to {value}'
            )
        return value

    def validate_quoted_price(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError('Price must be greater than 0')
        return value

    def validate(self, data):
        if 'status' in data and data['status'] == 'priced':
            if not data.get('quoted_price') and not self.instance.quoted_price:
                raise serializers.ValidationError({
                    'quoted_price': 'Price is required when setting status to priced'
                })
        return data
