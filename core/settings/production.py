"""
Django production settings for portfolio project.
"""

from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    'sameergul.pythonanywhere.com',
    'www.sameergul.pythonanywhere.com',
    'localhost',
    '127.0.0.1',
]

# Database
# Using SQLite for PythonAnywhere
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "https://67d0c3c1113bc04f72748c3b--sameergul.netlify.app",
    "http://localhost:5173",
    "http://localhost:3000",
]

CORS_ALLOW_CREDENTIALS = True

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'

# Email recipient for contact form
ADMIN_EMAIL = 'sameergul321@gmail.com'
