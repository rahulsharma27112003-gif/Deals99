#!/usr/bin/env python
"""
Run the Django development server
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'deals99_backend.config.settings.dev')
    django.setup()
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Run the development server
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])
