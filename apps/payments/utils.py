import requests
from django.conf import settings
from typing import Dict, Any, Optional
import json

class SafePayClient:
    def __init__(self):
        self.environment = getattr(settings, 'SAFEPAY_ENVIRONMENT', 'sandbox')
        self.public_key = getattr(settings, 'SAFEPAY_PUBLIC_KEY', 'sandbox_public_key')
        self.private_key = getattr(settings, 'SAFEPAY_PRIVATE_KEY', 'sandbox_private_key')
        self.BASE_URL = 'https://sandbox.api.getsafepay.com' if self.environment == 'sandbox' else 'https://api.getsafepay.com'
        self.API_VERSION = 'v1'

    def _get_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.private_key}',
            'Content-Type': 'application/json'
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/{self.API_VERSION}/{endpoint}"
        headers = self._get_headers()

        try:
            print(f"Making SafePay request to {url}")
            print(f"Request data: {json.dumps(data, indent=2)}")
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text[:1000]}")  # Print first 1000 chars
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"SafePay API error: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Error status code: {e.response.status_code}")
                try:
                    error_data = e.response.json()
                    print(f"Error response: {json.dumps(error_data, indent=2)}")
                except json.JSONDecodeError:
                    print(f"Raw error response: {e.response.text[:1000]}")  # Print first 1000 chars
            raise

    def create_checkout_session(
        self,
        amount: int,
        currency: str,
        order_id: str,
        cancel_url: str,
        success_url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a SafePay checkout session
        
        Args:
            amount: Amount in smallest currency unit (e.g., paisa for PKR)
            currency: Currency code (e.g., 'PKR')
            order_id: Your internal order ID
            cancel_url: URL to redirect on payment cancellation
            success_url: URL to redirect on payment success
            metadata: Additional data to attach to the payment
        
        Returns:
            Dict containing checkout session details
        """
        data = {
            'amount': amount,
            'currency': currency,
            'order_id': order_id,
            'cancel_url': cancel_url,  # URL is already formatted
            'success_url': success_url,  # URL is already formatted
            'environment': self.environment
        }
        if metadata:
            data['metadata'] = metadata

        # For sandbox, simulate a successful response
        if self.environment == 'sandbox':
            return {
                'tracker': f'sandbox_tracker_{order_id}',
                'checkout_url': success_url,  # In sandbox, just redirect to success URL
                'status': 'created'
            }

        return self._make_request('POST', 'checkout/session', data)

    def verify_payment(self, tracker: str) -> Dict[str, Any]:
        """
        Verify a payment using its tracker ID
        
        Args:
            tracker: SafePay payment tracker ID
        
        Returns:
            Dict containing payment verification details
        """
        # For sandbox, always return success
        if self.environment == 'sandbox':
            return {
                'status': 'paid',
                'tracker': tracker
            }

        return self._make_request('GET', f'checkout/session/{tracker}/verify')

    def create_refund(
        self,
        tracker: str,
        amount: int,
        reason: str
    ) -> Dict[str, Any]:
        """
        Create a refund for a payment
        
        Args:
            tracker: SafePay payment tracker ID
            amount: Amount to refund in smallest currency unit
            reason: Reason for the refund
        
        Returns:
            Dict containing refund details
        """
        data = {
            'amount': amount,
            'reason': reason
        }

        # For sandbox, simulate a successful refund
        if self.environment == 'sandbox':
            return {
                'status': 'refunded',
                'tracker': tracker,
                'amount': amount
            }

        return self._make_request('POST', f'payments/{tracker}/refund', data)

    def get_payment_details(self, tracker: str) -> Dict[str, Any]:
        """
        Get details of a payment
        
        Args:
            tracker: SafePay payment tracker ID
        
        Returns:
            Dict containing payment details
        """
        # For sandbox, return mock details
        if self.environment == 'sandbox':
            return {
                'status': 'paid',
                'tracker': tracker
            }

        return self._make_request('GET', f'payments/{tracker}')
