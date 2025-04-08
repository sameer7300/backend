import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.conf import settings
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)

# Configure Brevo API client
config = sib_api_v3_sdk.Configuration()
config.api_key['api-key'] = settings.BREVO_API_KEY

# SMTP configuration for direct SMTP usage if needed
BREVO_SMTP_CONFIG = {
    'host': 'smtp-relay.brevo.com',
    'port': 587,
    'username': '88a3a1001@smtp-brevo.com',
    'password': settings.BREVO_SMTP_PASSWORD,
}

def send_email_with_brevo(to_email, subject, html_content, sender_name=None, sender_email=None):
    """
    Send an email using Brevo API
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        html_content (str): HTML content of the email
        sender_name (str, optional): Sender name. Defaults to site name from settings.
        sender_email (str, optional): Sender email. Defaults to DEFAULT_FROM_EMAIL from settings.
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Create an instance of the API class
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(config))
        
        # Set up sender
        # Extract email from DEFAULT_FROM_EMAIL if it contains a name
        default_email = settings.DEFAULT_FROM_EMAIL
        if '<' in default_email and '>' in default_email:
            # Format is like "Name <email@example.com>"
            default_name = default_email.split('<')[0].strip()
            default_email = default_email.split('<')[1].split('>')[0].strip()
        else:
            default_name = settings.SITE_NAME
            
        sender = {
            "name": sender_name or default_name,
            "email": sender_email or default_email
        }
        
        # Set up recipient
        to = [{"email": to_email}]
        
        # Create the email request
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=to,
            html_content=html_content,
            sender=sender,
            subject=subject
        )
        
        # Send the email
        response = api_instance.send_transac_email(send_smtp_email)
        logger.info(f"Email sent successfully to {to_email} with message ID: {response.message_id}")
        return True
        
    except ApiException as e:
        logger.error(f"Exception when calling Brevo API: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error when sending email via Brevo: {e}")
        return False

def send_message_notification(recipient_email, sender_name, message_preview):
    """
    Send an email notification when a new message is received using Brevo
    """
    try:
        # Render the HTML template
        html_message = render_to_string('chat/email/new_message.html', {
            'sender_name': sender_name,
            'message_preview': message_preview,
            'site_url': settings.SITE_URL,
        })
        
        # Send the email using Brevo
        success = send_email_with_brevo(
            to_email=recipient_email,
            subject=f"New Message from {sender_name}",
            html_content=html_message
        )
        
        if success:
            logger.info(f"Email notification sent to {recipient_email} via Brevo")
            return True
        else:
            logger.warning(f"Failed to send email notification to {recipient_email} via Brevo")
            return False
            
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
        return False
