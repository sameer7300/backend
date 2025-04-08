from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
import json
import requests

class ResendEmailBackend(BaseEmailBackend):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get API key from settings or kwargs
        self.api_key = kwargs.get('api_key') or getattr(settings, 'RESEND_API_KEY', None)
        if not self.api_key:
            raise ValueError("No Resend API key found. Set RESEND_API_KEY in settings or pass it to the backend.")

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        num_sent = 0
        for message in email_messages:
            try:
                # Extract email content
                subject = message.subject
                body = message.body

                # Get sender email from settings or message
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or message.from_email
                if not from_email:
                    raise ValueError("No sender email found. Set DEFAULT_FROM_EMAIL in settings or specify in the message.")

                # Prepare the request
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
                
                data = {
                    'from': from_email,
                    'to': message.to,
                    'subject': subject,
                    'text': body,  # Always use text for now to ensure delivery
                }

                # Make direct API call
                print("Sending email with Resend:")
                print(f"From: {data['from']}")
                print(f"To: {data['to']}")
                print(f"Subject: {data['subject']}")
                
                response = requests.post(
                    'https://api.resend.com/emails',
                    headers=headers,
                    json=data
                )

                # Log the response
                print(f"Resend API Response Status: {response.status_code}")
                print(f"Response body: {response.text}")

                if response.status_code != 200:
                    raise Exception(f"Resend API error: {response.text}")

                num_sent += 1
            except Exception as e:
                print(f"Error sending email via Resend: {str(e)}")
                if not self.fail_silently:
                    raise e

        return num_sent
