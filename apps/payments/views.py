from django.utils import timezone
from django.db import transaction
from django.conf import settings
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.accounts.permissions import IsAdmin
from .models import (
    PaymentMethod,
    Transaction,
    Receipt,
    Refund,
    PaymentWebhook
)
from .serializers import (
    PaymentMethodSerializer,
    TransactionListSerializer,
    TransactionDetailSerializer,
    TransactionCreateSerializer,
    ReceiptSerializer,
    RefundSerializer,
    PaymentWebhookSerializer
)
from .utils import SafePayClient
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from apps.hiring.models import HiringRequest

# Set Stripe key directly for now
stripe.api_key = 'sk_test_51QP3gxFWlKllCGeE5PACApOXt50kbj1c15wFXfZULdLr2UuL45n7TMkiLmDXlXxCRZYjuCg6CNhKsZNzCdY8Wu0800vw7mjJDn'

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    try:
        data = request.data
        amount = data.get('amount')
        request_id = data.get('request_id')
        
        if not amount:
            return Response({'error': 'Amount is required'}, status=400)

        if not request_id:
            return Response({'error': 'Request ID is required'}, status=400)

        # Create a PaymentIntent with the order amount and currency
        intent = stripe.PaymentIntent.create(
            amount=amount,  # Amount in cents
            currency='usd',
            metadata={
                'user_id': request.user.id,
                'request_id': request_id
            }
        )

        return Response({
            'clientSecret': intent.client_secret
        })

    except Exception as e:
        return Response({
            'error': str(e)
        }, status=400)

@csrf_exempt
def webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = 'whsec_test_51QP3gxFWlKllCGeE5PACApOXt50kbj1c15wFXfZULdLr2UuL45n7TMkiLmDXlXxCRZYjuCg6CNhKsZNzCdY8Wu0800vw7mjJDn'
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        
        if event.type == 'payment_intent.succeeded':
            payment_intent = event.data.object
            print("Payment succeeded:", payment_intent.id)
            
            # Update request status
            request_id = payment_intent.metadata.get('request_id')
            if request_id:
                try:
                    hiring_request = HiringRequest.objects.get(id=request_id)
                    hiring_request.status = 'paid'
                    hiring_request.save()
                    print(f"Updated request {request_id} status to paid")
                except HiringRequest.DoesNotExist:
                    print(f"Request {request_id} not found")
                except Exception as e:
                    print(f"Error updating request {request_id}: {str(e)}")
            
        return HttpResponse(status=200)
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return HttpResponse(status=400)

class PaymentMethodViewSet(viewsets.ModelViewSet):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_staff:
            return PaymentMethod.objects.all()
        return PaymentMethod.objects.filter(is_active=True)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdmin]
        return super().get_permissions()

class TransactionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Transaction.objects.all()
        return Transaction.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return TransactionCreateSerializer
        elif self.action == 'list':
            return TransactionListSerializer
        return TransactionDetailSerializer

    def perform_create(self, serializer):
        # Generate a unique reference ID
        reference_id = f"TXN-{timezone.now().strftime('%Y%m%d%H%M%S')}-{self.request.user.id}"
        
        # Create transaction in pending state
        transaction = serializer.save(
            user=self.request.user,
            reference_id=reference_id,
            status='pending'
        )

        # Create SafePay checkout session if payment method is SafePay
        if transaction.payment_method.payment_type == 'safepay':
            try:
                # Initialize SafePay client
                safepay_client = SafePayClient()
                
                # Convert amount to paisa (smallest currency unit)
                amount_in_paisa = int(float(transaction.amount) * 100)
                
                # Create success and cancel URLs
                success_url = f"{settings.FRONTEND_URL}/hiring/requests/{transaction.hiring_request.id}?payment_status=success"
                cancel_url = f"{settings.FRONTEND_URL}/hiring/requests/{transaction.hiring_request.id}?payment_status=cancelled"
                
                # Create checkout session
                checkout_session = safepay_client.create_checkout_session(
                    amount=amount_in_paisa,
                    currency=transaction.currency,
                    order_id=transaction.reference_id,
                    cancel_url=cancel_url,
                    success_url=success_url,
                    metadata={
                        'user_id': str(transaction.user.id),
                        'hiring_request_id': str(transaction.hiring_request.id)
                    }
                )

                # Update transaction with SafePay details
                transaction.safepay_tracker = checkout_session['tracker']
                transaction.safepay_checkout_url = checkout_session['checkout_url']
                transaction.safepay_status = checkout_session['status']
                transaction.payment_data = checkout_session
                transaction.save()

            except Exception as e:
                transaction.status = 'failed'
                transaction.payment_data = {'error': str(e)}
                transaction.save()
                raise

    @action(detail=True, methods=['post'])
    def process_payment(self, request, pk=None):
        transaction_obj = self.get_object()
        
        if transaction_obj.status != 'pending':
            return Response(
                {'error': 'Transaction is not in pending state'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if transaction_obj.payment_method.payment_type == 'safepay':
            try:
                # Initialize SafePay client
                safepay_client = SafePayClient()
                
                # Verify payment with SafePay
                payment_details = safepay_client.verify_payment(
                    transaction_obj.safepay_tracker
                )

                if payment_details['status'] == 'paid':
                    transaction_obj.status = 'completed'
                    transaction_obj.safepay_status = payment_details['status']
                    transaction_obj.payment_data.update(payment_details)
                    transaction_obj.save()

                    # Create receipt
                    Receipt.objects.create(
                        transaction=transaction_obj,
                        receipt_number=f"RCP-{transaction_obj.reference_id}",
                        subtotal=transaction_obj.amount,
                        tax=0,  # Calculate tax as needed
                        total=transaction_obj.amount
                    )

                    return Response({
                        'message': 'Payment processed successfully',
                        'status': transaction_obj.status
                    })
                else:
                    transaction_obj.status = 'failed'
                    transaction_obj.safepay_status = payment_details['status']
                    transaction_obj.payment_data.update(payment_details)
                    transaction_obj.save()
                    
                    return Response({
                        'error': 'Payment verification failed',
                        'status': payment_details['status']
                    }, status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                transaction_obj.status = 'failed'
                transaction_obj.save()
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            # Handle other payment methods
            return Response(
                {'error': 'Unsupported payment method'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def request_refund(self, request, pk=None):
        transaction_obj = self.get_object()
        
        if transaction_obj.status != 'completed':
            return Response(
                {'error': 'Only completed transactions can be refunded'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RefundSerializer(
            data=request.data,
            context={'transaction': transaction_obj}
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            refund = serializer.save(transaction=transaction_obj)
            
            if transaction_obj.payment_method.payment_type == 'safepay':
                try:
                    # Initialize SafePay client
                    safepay_client = SafePayClient()
                    
                    # Convert amount to paisa
                    amount_in_paisa = int(float(refund.amount) * 100)
                    
                    # Process refund with SafePay
                    refund_details = safepay_client.create_refund(
                        tracker=transaction_obj.safepay_tracker,
                        amount=amount_in_paisa,
                        reason=refund.reason
                    )

                    refund.status = 'completed'
                    refund.refunded_at = timezone.now()
                    refund.refund_data = refund_details
                    refund.save()

                    # Update transaction status
                    transaction_obj.status = 'refunded'
                    transaction_obj.save()

                except Exception as e:
                    refund.status = 'failed'
                    refund.refund_data = {'error': str(e)}
                    refund.save()
                    raise

            return Response(
                RefundSerializer(refund).data,
                status=status.HTTP_201_CREATED
            )

class RefundViewSet(viewsets.ModelViewSet):
    serializer_class = RefundSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Refund.objects.all()
        return Refund.objects.filter(transaction__user=user)

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdmin]
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def process_refund(self, request, pk=None):
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can process refunds'},
                status=status.HTTP_403_FORBIDDEN
            )

        refund = self.get_object()
        
        if refund.status != 'pending':
            return Response(
                {'error': 'Refund is not in pending state'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transaction_obj = refund.transaction
        if transaction_obj.payment_method.payment_type == 'safepay':
            try:
                # Initialize SafePay client
                safepay_client = SafePayClient()
                
                # Convert amount to paisa
                amount_in_paisa = int(float(refund.amount) * 100)
                
                # Process refund with SafePay
                refund_details = safepay_client.create_refund(
                    tracker=transaction_obj.safepay_tracker,
                    amount=amount_in_paisa,
                    reason=refund.reason
                )

                refund.status = 'completed'
                refund.refunded_at = timezone.now()
                refund.refund_data = refund_details
                refund.save()

                # Update transaction status
                transaction_obj.status = 'refunded'
                transaction_obj.save()

                return Response({
                    'message': 'Refund processed successfully',
                    'status': refund.status
                })

            except Exception as e:
                refund.status = 'failed'
                refund.save()
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(
                {'error': 'Unsupported payment method for refund'},
                status=status.HTTP_400_BAD_REQUEST
            )

class PaymentWebhookViewSet(viewsets.ModelViewSet):
    queryset = PaymentWebhook.objects.all()
    serializer_class = PaymentWebhookSerializer
    permission_classes = [IsAdmin]

    @action(detail=False, methods=['post'])
    def handle_webhook(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        webhook = serializer.save()

        try:
            # Process the webhook based on event_type
            event_type = webhook.event_type
            payload = webhook.payload

            if event_type == 'payment.success':
                tracker = payload.get('tracker')
                if tracker:
                    # Initialize SafePay client
                    safepay_client = SafePayClient()
                    
                    # Verify payment with SafePay
                    payment_details = safepay_client.get_payment_details(tracker)
                    
                    transaction_obj = Transaction.objects.get(
                        safepay_tracker=tracker
                    )
                    
                    if payment_details['status'] == 'paid':
                        transaction_obj.status = 'completed'
                        transaction_obj.safepay_status = payment_details['status']
                        transaction_obj.payment_data.update(payment_details)
                        transaction_obj.save()

                        # Create receipt
                        Receipt.objects.create(
                            transaction=transaction_obj,
                            receipt_number=f"RCP-{transaction_obj.reference_id}",
                            subtotal=transaction_obj.amount,
                            tax=0,
                            total=transaction_obj.amount
                        )

            elif event_type == 'payment.failed':
                tracker = payload.get('tracker')
                if tracker:
                    transaction_obj = Transaction.objects.get(
                        safepay_tracker=tracker
                    )
                    transaction_obj.status = 'failed'
                    transaction_obj.safepay_status = 'failed'
                    transaction_obj.payment_data.update(payload)
                    transaction_obj.save()

            webhook.processed = True
            webhook.save()

            return Response({
                'message': 'Webhook processed successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            webhook.error_message = str(e)
            webhook.save()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
