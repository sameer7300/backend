"""
Django development settings for portfolio project.
"""

from .base import *
from datetime import timedelta

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# CORS settings
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',  # Vite dev server
    'http://localhost:3002',  # Alternative dev server port
]
CORS_ALLOW_CREDENTIALS = True

# Rest Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Debug toolbar settings
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.sameergul.com'
EMAIL_PORT = 465
EMAIL_HOST_USER = 'admin@sameergul.com'
EMAIL_HOST_PASSWORD = 'Silent12.321?'
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
DEFAULT_FROM_EMAIL = 'admin@sameergul.com'

# Site configuration
SITE_NAME = 'Sameer Gul Portfolio'
SITE_URL = 'http://localhost:5173'  # Frontend URL for links in emails

# Email recipient for contact form
ADMIN_EMAIL = 'sameergul321@gmail.com'
