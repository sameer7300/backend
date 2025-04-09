"""
Test contact form email functionality directly
Run with: python test_contact_form_direct.py
"""

import os
import django
import sys
import uuid

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.conf import settings
from core.email_utils import send_mail

def test_contact_email_direct():
    """Test sending a contact form email directly using our custom email utility"""
    print("Testing direct contact form email...")
    
    # Create unique test data
    unique_id = str(uuid.uuid4())[:8]
    test_data = {
        'name': f'Test User {unique_id}',
        'email': 'sameergul321@gmail.com',
        'subject': f'Test Contact Form {unique_id}',
        'message': f'This is a test message from the contact form test script. ID: {unique_id}'
    }
    
    print(f"\nTest data: {test_data}")
    
    # Create HTML content for the email
    html_content = f'''
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
            .container {{ background-color: #f5f5f5; border-radius: 8px; padding: 20px; margin: 20px 0; border: 1px solid #e0e0e0; }}
            .header {{ color: #2196f3; }}
            .field {{ margin-bottom: 10px; }}
            .field strong {{ display: inline-block; width: 80px; }}
            .message {{ background-color: #e0e0e0; padding: 15px; border-radius: 4px; margin-top: 15px; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <h2 class="header">New Contact Form Submission</h2>
        <div class="container">
            <div class="field"><strong>Subject:</strong> {test_data['subject']}</div>
            <div class="field"><strong>Name:</strong> {test_data['name']}</div>
            <div class="field"><strong>Email:</strong> {test_data['email']}</div>
            <div class="field"><strong>Message:</strong></div>
            <div class="message">{test_data['message']}</div>
        </div>
        <div class="footer">
            <p>This message was sent from the contact form on {settings.SITE_NAME}.</p>
        </div>
    </body>
    </html>
    '''
    
    # Plain text version for email clients that don't support HTML
    plain_text = f'''
New Contact Form Submission

Subject: {test_data['subject']}
Name: {test_data['name']}
Email: {test_data['email']}

Message:
{test_data['message']}

This message was sent from the contact form on {settings.SITE_NAME}.
'''
    
    print("\nUsing our custom email utility to send the email...")
    
    # Use our guaranteed-working email utility
    success = send_mail(
        subject=f'New Contact Form Submission: {test_data["subject"]}',
        message=plain_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ADMIN_EMAIL],
        html_message=html_content,
    )
    
    print(f"Email sending {'succeeded' if success else 'failed'}")
    return success

if __name__ == "__main__":
    # Run the test
    print("=== DIRECT CONTACT FORM EMAIL TEST ===\n")
    
    try:
        success = test_contact_email_direct()
        
        print(f"\n=== RESULTS: {'Success' if success else 'Failed'} ===")
        
        if success:
            print("Direct contact form email test completed successfully.")
            print("Please check your email inbox to confirm the email was delivered correctly.")
            print(f"The email should be sent to: {settings.ADMIN_EMAIL}")
            sys.exit(0)
        else:
            print("Direct contact form email test failed.")
            sys.exit(1)
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        sys.exit(1) 