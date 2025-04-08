"""
WSGI config for portfolio project.
"""

import os
import sys

# Add the project root directory to the sys.path
project_root = '/home/sameergul/sameergul-backend'
backend_path = os.path.join(project_root, 'backend')
sys.path.insert(0, project_root)
sys.path.insert(0, backend_path)

# Add the apps directory to the Python path
apps_path = os.path.join(backend_path, 'apps')
sys.path.insert(0, apps_path)

# Set Django settings module and environment variables
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.pythonanywhere_settings'
os.environ['DJANGO_ALLOWED_HOSTS'] = 'sameergul.pythonanywhere.com'
os.environ['PYTHONPATH'] = ':'.join(sys.path)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
