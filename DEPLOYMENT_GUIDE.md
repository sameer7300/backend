# Deployment Guide

This guide provides instructions for deploying the Django application and fixing email functionality.

## Deploying to Railway

1. **Commit and push your changes**:
   ```
   git add .
   git commit -m "Fixed email functionality with custom email utility"
   git push origin railway-config
   ```

2. **Create a pull request** to merge the changes into the main branch:
   - Go to your GitHub repository
   - Click on "Pull requests"
   - Click "New pull request"
   - Select the `railway-config` branch as the source
   - Select your main branch as the target
   - Create the pull request and merge it

3. **Deploy on Railway**:
   - Log in to your Railway dashboard
   - Select your project
   - Click on the "Deployments" tab
   - Click "Deploy" to deploy the latest changes

## Fixing Email Configuration

### Option 1: Environment Variables (Recommended)

Add these environment variables to your Railway project:

```
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
```

To add these variables:
1. Go to your Railway project dashboard
2. Click on the "Variables" tab
3. Add each of these environment variables
4. Deploy your application again

### Option 2: Custom Email Utility (Already Implemented)

We've created a custom email utility in `core/email_utils.py` that ensures emails are sent correctly. It uses the correct SMTP settings and bypasses Django's email configuration.

This utility provides two functions:
- `send_mail()`: Direct replacement for Django's send_mail function
- `send_template_mail()`: Enhanced function for sending emails with templates

All email-sending code in the application has been updated to use this utility, so emails should work correctly even if the environment variables aren't set.

## Testing Email Functionality

After deployment, you can test email functionality using these methods:

1. **Test the contact form**:
   - Go to your website
   - Fill out and submit the contact form
   - Check if you receive the contact form submission email

2. **Test user registration/verification**:
   - Register a new user on your website
   - Check if you receive the verification email

3. **Run test scripts locally**:
   - `python test_email_utils.py` - Tests the email utility directly
   - `python test_email_verification.py` - Tests verification email sending
   - `python test_contact_form_direct.py` - Tests contact form email directly

## Troubleshooting

If emails still don't work after deployment:

1. **Check logs**:
   - Check your Railway logs for any email-related errors

2. **Verify environment variables**:
   - Make sure all environment variables are set correctly
   - Double-check the values for EMAIL_PORT, EMAIL_USE_TLS, and EMAIL_USE_SSL

3. **Test with direct SMTP**:
   - SSH into your Railway instance
   - Run `python test_email_utils.py` to test email functionality directly

4. **Check email server configuration**:
   - Ensure your email server (mail.sameergul.com) allows connections from Railway's IP addresses
   - Verify that the email account credentials are correct 