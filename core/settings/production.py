"""

Django production settings for portfolio project.

"""



import os

import dj_database_url

from .base import *



DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'



# Read ALLOWED_HOSTS from environment variable or use default

ALLOWED_HOSTS_ENV = os.environ.get('DJANGO_ALLOWED_HOSTS', '')

ALLOWED_HOSTS = ALLOWED_HOSTS_ENV.split(',') if ALLOWED_HOSTS_ENV else []



# Always include these hosts regardless of environment variable

ALLOWED_HOSTS.extend([

    'portfolio-backend-production-c0e6.up.railway.app',

    'localhost',

    '127.0.0.1',
    'sameergul.com',
    'https://sameergul.com',
    '*',  # Temporarily allow all hosts for initial deployment

])



# Ensure there are no duplicate entries

ALLOWED_HOSTS = list(set(ALLOWED_HOSTS))



# Database configuration

# Check if we should use SQLite (for development/testing on Railway)

if os.environ.get('USE_SQLITE', 'False').lower() == 'true':

    # Use SQLite

    DATABASES = {

        'default': {

            'ENGINE': 'django.db.backends.sqlite3',

            'NAME': BASE_DIR / 'db.sqlite3',

        }

    }

else:

    # Use PostgreSQL from DATABASE_URL

    DATABASES = {

        'default': dj_database_url.config(

            default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'),

            conn_max_age=600,

            conn_health_checks=True,

        )

    }



# Security settings - temporarily disabled for initial deployment

SECURE_SSL_REDIRECT = False

SESSION_COOKIE_SECURE = False 

CSRF_COOKIE_SECURE = False

SECURE_BROWSER_XSS_FILTER = True

SECURE_CONTENT_TYPE_NOSNIFF = True

X_FRAME_OPTIONS = 'DENY'



# CORS settings - temporarily allow all origins for initial deployment

CORS_ALLOWED_ORIGINS = [

    'https://portfolio-backend-production-c0e6.up.railway.app',

    'http://portfolio-backend-production-c0e6.up.railway.app',

    os.environ.get('FRONTEND_URL', 'https://portfolio.sameergul.com'),

    "https://67d0c3c1113bc04f72748c3b--sameergul.netlify.app",

    "http://localhost:5173",

    "http://localhost:3000",

]

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True



# Static files

STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_ROOT = BASE_DIR / 'media'



# Email configuration - use proper SMTP for production

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'mail.sameergul.com'

EMAIL_PORT = 587  # Changed from 465 to 587 for submission with STARTTLS

EMAIL_HOST_USER = 'admin@sameergul.com'

EMAIL_HOST_PASSWORD = 'Silent12.321?'

EMAIL_USE_TLS = True  # Use TLS with port 587

EMAIL_USE_SSL = False  # SSL and TLS cannot be used together

DEFAULT_FROM_EMAIL = 'admin@sameergul.com'

EMAIL_TIMEOUT = 30  # Set a longer timeout

EMAIL_FILE_PATH = BASE_DIR / 'sent_emails'  # For fallback file-based email backend



# Additional email settings

EMAIL_SSL_CERTFILE = None  # Disable SSL certificate verification

EMAIL_SSL_KEYFILE = None



# Configure logging for email debugging

LOGGING = {

    'version': 1,

    'disable_existing_loggers': False,

    'handlers': {

        'console': {

            'class': 'logging.StreamHandler',

        },

    },

    'loggers': {

        'django.request': {

            'handlers': ['console'],

            'level': 'DEBUG',

            'propagate': True,

        },

        'django.security': {

            'handlers': ['console'],

            'level': 'DEBUG',

            'propagate': True,

        },

        'django.template': {

            'handlers': ['console'],

            'level': 'DEBUG',

            'propagate': True,

        },

        'django.server': {

            'handlers': ['console'],

            'level': 'DEBUG',

            'propagate': True,

        },

        'django.db.backends': {

            'handlers': ['console'],

            'level': 'DEBUG',

            'propagate': True,

        },

        'django.utils.autoreload': {

            'handlers': ['console'],

            'level': 'INFO',

            'propagate': True,

        },

    }

}



# Site configuration

SITE_NAME = 'Sameer Gul Portfolio'

SITE_URL = os.environ.get('FRONTEND_URL', 'https://portfolio.sameergul.com')



# Email recipient for contact form

ADMIN_EMAIL = 'sameergul321@gmail.com'


