"""
Test contact form email functionality
Run with: python test_contact_form.py
"""

import os
import django
import sys
import json
import uuid

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.conf import settings
from rest_framework.test import APIClient
from apps.portfolio.models import Contact

# Create a test client
client = APIClient()

def test_contact_form_submission():
    """Test the contact form submission and email sending"""
    print("Testing contact form submission...")
    
    # Create unique test data
    unique_id = str(uuid.uuid4())[:8]
    test_data = {
        'name': f'Test User {unique_id}',
        'email': 'sameergul321@gmail.com',
        'subject': f'Test Contact Form {unique_id}',
        'message': f'This is a test message from the contact form test script. ID: {unique_id}'
    }
    
    # Print the request data
    print(f"\nPOST data: {json.dumps(test_data, indent=2)}")
    
    # Make a POST request to the contact form endpoint
    response = client.post('/api/v1/portfolio/contacts/', test_data, format='json')
    
    # Check the response
    success = response.status_code == 201
    print(f"\nResponse status code: {response.status_code}")
    
    if success:
        print("Contact form submission successful!")
        print(f"Response data: {json.dumps(response.json(), indent=2)}")
        
        # Verify in the database
        try:
            contact = Contact.objects.get(subject=test_data['subject'])
            print(f"\nVerified in database: Contact #{contact.id} created successfully")
        except Contact.DoesNotExist:
            print("\nError: Contact not found in the database!")
            success = False
    else:
        print(f"Contact form submission failed!")
        print(f"Response data: {response.content.decode()}")
    
    print("\nIf successful, check your email inbox for the contact form notification.")
    print(f"The subject should be: New Contact Form Submission: {test_data['subject']}")
    
    return success

if __name__ == "__main__":
    # Run the test
    print("=== CONTACT FORM TEST ===\n")
    
    try:
        success = test_contact_form_submission()
        
        print(f"\n=== RESULTS: {'Success' if success else 'Failed'} ===")
        
        if success:
            print("Contact form test completed successfully.")
            print("Please check your email inbox to confirm the notification was delivered correctly.")
            sys.exit(0)
        else:
            print("Contact form test failed. Check the error message above.")
            sys.exit(1)
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        sys.exit(1) 