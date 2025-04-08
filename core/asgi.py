"""
ASGI config for portfolio project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from django.core.asgi import get_asgi_application

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(env_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')

application = get_asgi_application()
