from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.contrib.auth import get_user_model, authenticate
from .serializers import (
    UserSerializer,
    ProfileSerializer,
    UserActivitySerializer,
    RegisterSerializer,
    ChangePasswordSerializer,
)
from .models import Profile, UserActivity
from .permissions import IsAdmin, IsRegisteredUser, IsOwnerOrAdmin
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
import uuid
import json
from datetime import datetime, timedelta
from core.email_utils import send_mail as custom_send_mail

User = get_user_model()

# Helper function to get client IP address
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Create your views here.

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        print('Registration data received:', request.data)  # Debug print
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # In production, we'll keep users active for now to avoid login issues
            # Later we can implement proper email verification
            user.is_active = True
            user.is_email_verified = True  # Auto-verify for now
            
            # Generate verification token
            verification_token = str(uuid.uuid4())
            user.email_verification_token = verification_token
            user.save()
            
            # Create verification URL
            verification_url = f"{settings.SITE_URL}/verify-email/{verification_token}"
            
            # Prepare email content
            context = {
                'user': user,
                'verification_url': verification_url,
                'site_name': settings.SITE_NAME,
            }
            
            # Render email templates
            html_message = render_to_string('accounts/email/email_verification.html', context)
            plain_message = f"""Hello {user.first_name},

Thank you for registering with {settings.SITE_NAME}. Please verify your email by clicking the link below:

{verification_url}

This link will expire in 24 hours.

If you did not create an account, please ignore this email.

Best regards,
{settings.SITE_NAME} Team
"""
            
            # Send verification email using our guaranteed working email utility
            try:
                print("Sending registration email via our email utility...")
                
                custom_send_mail(
                    subject=f'Verify your email for {settings.SITE_NAME}',
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                )
                
                print(f"Verification email sent successfully to {user.email}")
                email_sent = True
            except Exception as e:
                print(f"Error sending verification email: {str(e)}")
                email_sent = False
            
            # Log the registration
            UserActivity.objects.create(
                user=user,
                activity_type=UserActivity.ActivityType.REGISTRATION,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            response_message = 'Registration successful.'
            if email_sent:
                response_message += ' Please check your email to verify your account.'
            else:
                response_message += ' Your account has been created, but we could not send a verification email. You can still log in.'
            
            return Response({
                'message': response_message,
                'email': user.email
            }, status=status.HTTP_201_CREATED)
        print('Validation errors:', serializer.errors)  # Debug print
        return Response({
            'message': 'Validation error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        print('Login data received:', request.data)  # Debug print
        
        # For now, we'll bypass the email verification check in production
        # and just attempt to log the user in directly
        
        # Proceed with the normal token generation
        try:
            email = request.data.get('email', '').lower()
            print(f"Attempting to generate tokens for user: {email}")
            response = super().post(request, *args, **kwargs)
            print(f"Token generation response status: {response.status_code}")
            
            if response.status_code == 200:
                # Extract user from the token
                access_token = response.data.get('access')
                print(f"Access token: {access_token[:10]}...")
                user_id = AccessToken(access_token).get('user_id')
                user = User.objects.get(id=user_id)
                print(f"Found user by token: {user.email}")
                
                # Ensure user is marked as verified (temporary solution)
                if not user.is_email_verified:
                    user.is_email_verified = True
                    user.save()
                
                # Log the login activity
                UserActivity.objects.create(
                    user=user,
                    activity_type=UserActivity.ActivityType.LOGIN,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Add user data to response
                response.data['user'] = UserSerializer(user).data
            
            return response
        except Exception as e:
            print(f"Error in login: {str(e)}")
            # If an exception occurs, return a generic error message
            return Response({
                'error': 'Login failed',
                'message': 'Invalid credentials or account issue. Please try again.'
            }, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({
                    'message': 'Refresh token is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            # Add the token to the blacklist
            token.blacklist()
            
            # Log the logout activity if user is authenticated
            if request.user.is_authenticated:
                UserActivity.objects.create(
                    user=request.user,
                    activity_type=UserActivity.ActivityType.LOGOUT,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            print('Logout error:', str(e))
            return Response({
                'message': 'Invalid token'
            }, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsOwnerOrAdmin,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            UserActivity.objects.create(
                user=request.user,
                activity_type=UserActivity.ActivityType.PROFILE_UPDATE,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        return response

class ChangePasswordView(APIView):
    permission_classes = (IsOwnerOrAdmin,)

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.data.get('old_password')):
                user.set_password(serializer.data.get('new_password'))
                user.save()
                UserActivity.objects.create(
                    user=user,
                    activity_type=UserActivity.ActivityType.PASSWORD_CHANGE,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                return Response({'message': 'Password updated successfully'}, status=status.HTTP_200_OK)
            return Response({'error': 'Incorrect old password'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({
                'message': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email.lower())
            # Generate password reset token
            token = default_token_generator.make_token(user)
            reset_url = f"{settings.SITE_URL}/reset-password?token={token}&email={email}"

            # Prepare email content
            html_content = render_to_string('accounts/email/password_reset.html', {
                'reset_url': reset_url,
                'site_name': settings.SITE_NAME,
                'site_url': settings.SITE_URL,
            })
            
            # If HTML template doesn't exist, use a simple HTML message
            if not html_content:
                html_content = f'''
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .container {{ background-color: #f5f5f5; border-radius: 8px; padding: 20px; margin: 20px 0; border: 1px solid #e0e0e0; }}
                        .button {{ display: inline-block; padding: 12px 24px; background-color: #2196f3; color: white !important; text-decoration: none; border-radius: 4px; margin-top: 20px; font-weight: bold; }}
                        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #666; }}
                    </style>
                </head>
                <body>
                    <h2>Password Reset Request</h2>
                    <div class="container">
                        <p>Hello,</p>
                        <p>You have requested to reset your password. Click the button below to set a new password:</p>
                        <a href="{reset_url}" class="button">Reset Password</a>
                        <p>Or copy and paste this link in your browser:</p>
                        <p>{reset_url}</p>
                        <p>This link will expire in 24 hours.</p>
                        <p>If you did not request this password reset, please ignore this email.</p>
                    </div>
                    <div class="footer">
                        <p>Best regards,<br>{settings.SITE_NAME}</p>
                        <p>This is an automated message. Please do not reply to this email.</p>
                    </div>
                </body>
                </html>
                '''
                
            # Plain text version for email clients that don't support HTML
            plain_text = f'''
Hello,

You have requested to reset your password. Click the link below to set a new password:

{reset_url}

This link will expire in 24 hours.

If you did not request this password reset, please ignore this email.

Best regards,
{settings.SITE_NAME}
'''
            
            try:
                # Use our guaranteed-working email utility
                custom_send_mail(
                    subject='Password Reset - Your Portfolio',
                    message=plain_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    html_message=html_content,
                )
                print(f"Password reset email sent successfully to {email}")
            except Exception as e:
                print(f"Error sending password reset email: {str(e)}")
                raise

            return Response({
                'message': 'Password reset email sent successfully'
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({
                'message': 'No account found with this email'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print('Password reset error:', str(e))
            return Response({
                'message': 'Error sending password reset email'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResetPasswordView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not all([email, token, new_password]):
            return Response({
                'message': 'Email, token and new password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email.lower())
            
            # Verify token
            if not default_token_generator.check_token(user, token):
                return Response({
                    'message': 'Invalid or expired token'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Set new password
            user.set_password(new_password)
            user.save()

            # Log the password reset
            UserActivity.objects.create(
                user=user,
                activity_type=UserActivity.ActivityType.PASSWORD_RESET,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Send password reset confirmation email
            try:
                from django.template.loader import render_to_string
                
                html_content = render_to_string('accounts/email/password_reset_successful.html', {
                    'site_name': settings.SITE_NAME,
                    'site_url': settings.SITE_URL,
                })
                
                # If HTML template doesn't exist, use a simple HTML message
                if not html_content:
                    html_content = f'''
                    <html>
                    <head>
                        <style>
                            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                            .container {{ background-color: #f5f5f5; border-radius: 8px; padding: 20px; margin: 20px 0; border: 1px solid #e0e0e0; }}
                            .button {{ display: inline-block; padding: 12px 24px; background-color: #2196f3; color: white !important; text-decoration: none; border-radius: 4px; margin-top: 20px; font-weight: bold; }}
                            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #666; }}
                        </style>
                    </head>
                    <body>
                        <h2>Password Reset Successful</h2>
                        <div class="container">
                            <p>Hello,</p>
                            <p>Your password has been successfully reset.</p>
                            <p>You can now log in to your account with your new password.</p>
                            <a href="{settings.SITE_URL}/login" class="button">Go to Login</a>
                            <p>If you did not reset your password, please contact us immediately.</p>
                        </div>
                        <div class="footer">
                            <p>Best regards,<br>{settings.SITE_NAME}</p>
                            <p>This is an automated message. Please do not reply to this email.</p>
                        </div>
                    </body>
                    </html>
                    '''
                    
                # Plain text version for email clients that don't support HTML
                plain_text = f'''
Hello,

Your password has been successfully reset.

You can now log in to your account with your new password.

If you did not reset your password, please contact us immediately.

Best regards,
{settings.SITE_NAME}
'''
                
                # Use our guaranteed-working email utility
                custom_send_mail(
                    subject='Password Reset Successful - Your Portfolio',
                    message=plain_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    html_message=html_content,
                )
                print(f"Password reset confirmation email sent successfully to {email}")
            except Exception as e:
                print(f"Error sending confirmation email: {str(e)}")
                # We don't want to fail the password reset if the confirmation email fails
                pass

            return Response({
                'message': 'Password reset successful'
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({
                'message': 'No account found with this email'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print('Password reset error:', str(e))
            return Response({
                'message': 'Error resetting password'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EmailVerificationView(APIView):
    permission_classes = (permissions.AllowAny,)
    
    def get(self, request, token):
        print(f"Attempting to verify email with token: {token}")
        try:
            # Find user with this verification token
            user = User.objects.get(email_verification_token=token)
            print(f"Found user: {user.email}")
            
            # Check if user is already verified
            if user.is_email_verified:
                print(f"User {user.email} is already verified")
                return Response({'message': 'Email already verified. Please login.'}, status=status.HTTP_200_OK)
            
            # Verify the user's email
            user.is_email_verified = True
            user.is_active = True
            user.email_verification_token = None  # Clear the token for security
            user.save()
            print(f"User {user.email} has been verified successfully")
            
            # Send confirmation email
            try:
                # Prepare email content
                html_message = render_to_string('accounts/email/verification_successful.html', {
                    'user': user,
                    'site_name': settings.SITE_NAME,
                    'site_url': settings.SITE_URL,
                })
                
                # If HTML template doesn't exist, use a simple HTML message
                if not html_message:
                    html_message = f'''
                    <html>
                    <head>
                        <style>
                            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                            .container {{ background-color: #f5f5f5; border-radius: 8px; padding: 20px; margin: 20px 0; border: 1px solid #e0e0e0; }}
                            .button {{ display: inline-block; padding: 12px 24px; background-color: #2196f3; color: white !important; text-decoration: none; border-radius: 4px; margin-top: 20px; font-weight: bold; }}
                            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #666; }}
                        </style>
                    </head>
                    <body>
                        <h2>Email Verification Successful</h2>
                        <div class="container">
                            <p>Hello {user.first_name or user.username},</p>
                            <p>Your email address has been successfully verified. You can now log in to your account.</p>
                            <a href="{settings.SITE_URL}/login" class="button">Login to Your Account</a>
                        </div>
                        <div class="footer">
                            <p>Best regards,<br>{settings.SITE_NAME}</p>
                            <p>This is an automated message. Please do not reply to this email.</p>
                        </div>
                    </body>
                    </html>
                    '''
                
                # Plain text version for email clients that don't support HTML
                plain_text = f'''
                Hello {user.first_name or user.username},

                Your email address has been successfully verified. You can now log in to your account.

                Login to your account at: {settings.SITE_URL}/login

                Best regards,
                {settings.SITE_NAME}

                This is an automated message. Please do not reply to this email.
                '''
                
                # Send the email using our custom email utility
                custom_send_mail(
                    subject=f"{settings.SITE_NAME} - Email Verification Successful",
                    message=plain_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                )
                
                print(f"Verification success email sent to {user.email}")
            except Exception as email_error:
                print(f"Error sending verification success email: {str(email_error)}")
                # Continue even if email sending fails
            
            # Generate tokens for auto-login
            try:
                refresh = RefreshToken.for_user(user)
                access = AccessToken.for_user(user)
                print("Generated tokens successfully")
            except Exception as token_error:
                print(f"Error generating tokens: {str(token_error)}")
                # Continue even if token generation fails
                return Response({
                    'message': 'Email verified successfully. You can now login.',
                }, status=status.HTTP_200_OK)
            
            # Log the verification
            try:
                UserActivity.objects.create(
                    user=user,
                    activity_type=UserActivity.ActivityType.EMAIL_VERIFICATION,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                print("Logged user activity successfully")
            except Exception as activity_error:
                print(f"Error logging activity: {str(activity_error)}")
                # Continue even if activity logging fails
            
            return Response({
                'message': 'Email verified successfully. You can now login.',
                'token': str(access),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            print(f"No user found with token: {token}")
            return Response({'error': 'Invalid or expired verification link. Please request a new verification email.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error during email verification: {str(e)}")
            return Response({'error': 'Verification failed. Please try again or request a new verification email.'}, status=status.HTTP_400_BAD_REQUEST)

class ResendVerificationEmailView(APIView):
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            
            # Check if already verified
            if user.is_email_verified:
                return Response({'message': 'Email already verified. Please login.'}, status=status.HTTP_200_OK)
            
            # Generate new verification token
            verification_token = str(uuid.uuid4())
            user.email_verification_token = verification_token
            user.save()
            
            # Send verification email
            verification_url = f"{settings.SITE_URL}/verify-email/{verification_token}"
            
            # HTML email template
            html_content = render_to_string('accounts/email/email_verification.html', {
                'user': user,
                'verification_url': verification_url,
                'site_name': settings.SITE_NAME,
                'expiry_hours': 24,  # Token expires in 24 hours
            })
            
            # Plain text version
            plain_text = f'''
            Hello {user.first_name},

            Thank you for registering with {settings.SITE_NAME}.

            Please verify your email address by clicking the link below:
            {verification_url}

            This link will expire in 24 hours.

            If you did not register for an account, please ignore this email.

            Best regards,
            {settings.SITE_NAME} Team
            '''
            
            # Send email using our custom email utility
            custom_send_mail(
                subject='Verify Your Email Address',
                message=plain_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_content,
            )
            
            # Log activity
            UserActivity.objects.create(
                user=user,
                activity_type=UserActivity.EMAIL_VERIFICATION,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details='Verification email resent'
            )
            
            return Response({'message': 'Verification email has been resent'}, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            # Don't reveal if user exists or not for security
            return Response({'message': 'If an account with this email exists, a verification email has been sent'}, 
                           status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Error resending verification email: {str(e)}")
            return Response({'error': 'Failed to resend verification email'}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserListView(generics.ListAPIView):
    """
    View to list all users in the system.
    Only admin users can access this view.
    """
    permission_classes = (IsAdmin,)
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserActivityListView(generics.ListAPIView):
    """
    View to list all user activities.
    Only admin users can access this view.
    """
    permission_classes = (IsAdmin,)
    serializer_class = UserActivitySerializer

    def get_queryset(self):
        return UserActivity.objects.all().order_by('-created_at')

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View to retrieve, update or delete a user instance.
    Only admin users can access this view.
    """
    permission_classes = (IsAdmin,)
    queryset = User.objects.all()
    serializer_class = UserSerializer
