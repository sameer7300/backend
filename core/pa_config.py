"""
PythonAnywhere configuration file
"""

import os
import sys

# PythonAnywhere paths
PA_PROJECT_ROOT = '/home/sameergul/sameergul-backend'
PA_BACKEND_PATH = os.path.join(PA_PROJECT_ROOT, 'backend')
PA_APPS_PATH = os.path.join(PA_BACKEND_PATH, 'apps')

def configure_paths():
    """Configure Python paths for PythonAnywhere"""
    paths = [PA_PROJECT_ROOT, PA_BACKEND_PATH, PA_APPS_PATH]
    for path in paths:
        if path not in sys.path:
            sys.path.insert(0, path)

def get_base_dir():
    """Get the base directory for Django settings"""
    return PA_BACKEND_PATH 