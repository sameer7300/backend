"""
Email utility functions for the application.
This provides a consistent way to send emails using the correct SMTP settings.
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
from django.core.mail import send_mail as django_send_mail
import logging

logger = logging.getLogger(__name__)

# Define guaranteed working email settings
SMTP_HOST = 'mail.sameergul.com'
SMTP_PORT = 587  # Use port 587 with STARTTLS
SMTP_USER = 'admin@sameergul.com'
SMTP_PASSWORD = 'Silent12.321?'
DEFAULT_FROM = 'admin@sameergul.com'

def send_mail(subject, message, from_email=None, recipient_list=None, html_message=None,
             fail_silently=False):
    """
    Send an email with guaranteed working settings.
    This is a drop-in replacement for django.core.mail.send_mail.
    """
    # Set defaults
    from_email = from_email or DEFAULT_FROM
    recipient_list = recipient_list or [settings.ADMIN_EMAIL]
    
    try:
        # Log the attempt
        logger.info(f"Sending email to {recipient_list} with subject: {subject}")
        
        # Create message
        message_obj = MIMEMultipart('alternative')
        message_obj['Subject'] = subject
        message_obj['From'] = from_email
        message_obj['To'] = ', '.join(recipient_list)
        
        # Add plain text part
        text_part = MIMEText(message, 'plain')
        message_obj.attach(text_part)
        
        # Add HTML part if provided
        if html_message:
            html_part = MIMEText(html_message, 'html')
            message_obj.attach(html_part)
        
        # Connect to server
        logger.debug(f"Connecting to SMTP server {SMTP_HOST}:{SMTP_PORT}")
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
        
        # Start TLS
        logger.debug("Starting TLS")
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        server.starttls(context=context)
        
        # Login
        logger.debug(f"Logging in as {SMTP_USER}")
        server.login(SMTP_USER, SMTP_PASSWORD)
        
        # Send email
        logger.debug(f"Sending email from {from_email} to {recipient_list}")
        server.sendmail(from_email, recipient_list, message_obj.as_string())
        server.quit()
        
        logger.info(f"Email sent successfully to {recipient_list}")
        return True
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        if not fail_silently:
            raise
        return False

def send_template_mail(subject, template_txt, template_html, context, from_email=None, 
                     recipient_list=None, fail_silently=False):
    """
    Send an email using templates with context.
    """
    from django.template import Template, Context
    from django.template.loader import get_template
    
    # Process templates
    try:
        # Try to load the templates first
        try:
            txt_template = get_template(template_txt)
            html_template = get_template(template_html) if template_html else None
        except Exception as e:
            # Fall back to treating the input as actual template content
            txt_template = Template(template_txt)
            html_template = Template(template_html) if template_html else None
        
        # Render templates with context
        context_obj = Context(context) if isinstance(context, dict) else context
        message = txt_template.render(context_obj)
        html_message = html_template.render(context_obj) if html_template else None
        
        # Send the email
        return send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=fail_silently
        )
    except Exception as e:
        logger.error(f"Error rendering email templates: {str(e)}")
        if not fail_silently:
            raise
        return False 