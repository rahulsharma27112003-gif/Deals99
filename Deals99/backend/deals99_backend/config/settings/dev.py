from .base import *

# Development overrides
DEBUG = True
CORS_ALLOW_ALL_ORIGINS = True

# Use in-memory cache locally so tests/dev work without Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
