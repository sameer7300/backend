from django.http import HttpResponse
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def test_email(request):
    """A simple view to test email sending functionality."""
    try:
        # Log the email settings
        logger.info(f"Email settings: HOST={settings.EMAIL_HOST}, PORT={settings.EMAIL_PORT}, USER={settings.EMAIL_HOST_USER}")
        logger.info(f"TLS={settings.EMAIL_USE_TLS}, SSL={settings.EMAIL_USE_SSL}")
        
        # Try to send a test email
        send_mail(
            'Test Email from Portfolio Site',
            'This is a test email to verify that the email functionality is working correctly.',
            settings.DEFAULT_FROM_EMAIL,
            ['sameergul321@gmail.com'],
            fail_silently=False,
        )
        
        logger.info("Email sent successfully!")
        return HttpResponse("<h1>Email sent successfully!</h1><p>Check sameergul321@gmail.com for the test email.</p>")
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return HttpResponse(f"<h1>Error sending email</h1><p>Error: {str(e)}</p>")
