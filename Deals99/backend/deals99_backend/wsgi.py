"""
WSGI config for deals99_backend project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'deals99_backend.config.settings.prod')

application = get_wsgi_application()
