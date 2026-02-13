#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'deals99_backend.config.settings.dev')
django.setup()

from django.urls import resolve
from django.test import Client


def main():
    """Simple manual URL resolution check; not part of automated test suite."""
    try:
        match = resolve('/api/products/')
        print(f"OK URL /api/products/ resolved to: {match.func.__name__}")
    except Exception as e:
        print(f"ERROR URL /api/products/ error: {e}")

    client = Client()
    response = client.get('/api/products/')
    print(f"Response status: {response.status_code}")
    print(f"Response URL: {response.url if hasattr(response, 'url') else 'N/A'}")


if __name__ == "__main__":
    main()
