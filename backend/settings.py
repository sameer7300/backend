"""
This file is deprecated. All settings have been moved to core/settings/
Import all settings from core.settings to maintain compatibility
"""

from core.settings import *  # This will now import from core/settings/__init__.py

# Override any settings here if needed
ALLOWED_HOSTS = ['sameergul.pythonanywhere.com', 'localhost', '127.0.0.1']

CORS_ALLOWED_ORIGINS = [
    "https://67d0c3c1113bc04f72748c3b--sameergul.netlify.app/",  # Update this with your Netlify domain once deployed
    "http://localhost:5173",  # For local development
    "http://localhost:3000",
]

CORS_ALLOW_CREDENTIALS = True 