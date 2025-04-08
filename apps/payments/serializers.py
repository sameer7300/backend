from rest_framework import serializers
from django.utils import timezone
from .models import (
    PaymentMethod,
    Transaction,
    Receipt,
    Refund,
    PaymentWebhook
)

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'name', 'payment_type', 'description',
            'instructions', 'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']

class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = [
            'id', 'receipt_number', 'subtotal',
            'tax', 'total', 'notes', 'generated_at'
        ]
        read_only_fields = ['generated_at']

class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = [
            'id', 'transaction', 'amount', 'reason',
            'status', 'refund_data', 'refunded_at',
            'created_at'
        ]
        read_only_fields = ['created_at', 'refunded_at']

    def validate_amount(self, value):
        transaction = self.context['transaction']
        if value > transaction.amount:
            raise serializers.ValidationError(
                "Refund amount cannot be greater than transaction amount"
            )
        return value

class TransactionListSerializer(serializers.ModelSerializer):
    payment_method_name = serializers.CharField(
        source='payment_method.name',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = Transaction
        fields = [
            'id', 'reference_id', 'amount', 'currency',
            'status', 'status_display', 'payment_method_name',
            'created_at'
        ]
        read_only_fields = ['created_at']

class TransactionDetailSerializer(serializers.ModelSerializer):
    payment_method = PaymentMethodSerializer(read_only=True)
    payment_method_id = serializers.PrimaryKeyRelatedField(
        queryset=PaymentMethod.objects.filter(is_active=True),
        write_only=True,
        source='payment_method'
    )
    receipt = ReceiptSerializer(read_only=True)
    refunds = RefundSerializer(many=True, read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'hiring_request', 'payment_method',
            'payment_method_id', 'amount', 'currency', 'status',
            'status_display', 'reference_id', 'payment_data',
            'receipt', 'refunds', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user', 'reference_id', 'created_at',
            'updated_at'
        ]

class TransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'hiring_request', 'payment_method',
            'amount', 'currency'
        ]

    def validate_hiring_request(self, value):
        user = self.context['request'].user
        if value.user != user and not user.is_staff:
            raise serializers.ValidationError(
                "You can only create transactions for your own hiring requests"
            )
        return value

    def validate_payment_method(self, value):
        if not value.is_active:
            raise serializers.ValidationError(
                "Selected payment method is not active"
            )
        return value

class PaymentWebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentWebhook
        fields = [
            'id', 'event_type', 'payload', 'processed',
            'error_message', 'created_at'
        ]
        read_only_fields = ['created_at']
