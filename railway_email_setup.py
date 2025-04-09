"""
Railway Email Configuration Script

This script provides the correct email settings to be applied to Railway deployment.
You can copy these environment variables to your Railway project's environment variables.

Run with: python railway_email_setup.py
"""

print("=== RAILWAY EMAIL CONFIGURATION ===")
print("""
To fix email functionality in your Railway deployment, add the following 
environment variables to your Railway project:

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mail.sameergul.com
EMAIL_PORT=587
EMAIL_HOST_USER=admin@sameergul.com
EMAIL_HOST_PASSWORD=Silent12.321?
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=admin@sameergul.com
EMAIL_TIMEOUT=30
ADMIN_EMAIL=sameergul321@gmail.com

Instructions:
1. Go to your Railway project dashboard
2. Click on the "Variables" tab
3. Add or update each of these environment variables
4. Deploy your application again

These settings will ensure your application can send emails successfully.
""") 