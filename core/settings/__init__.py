"""
Django settings package initialization.
Import all settings from the appropriate environment module.
"""

import os
import socket

# Check if we're running on PythonAnywhere
if 'pythonanywhere' in socket.gethostname():
    from .production import *
else:
    from .local import *  # This will import all settings from local.py by default
