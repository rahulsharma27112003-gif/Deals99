import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'deals99_backend.config.settings.prod')

app = Celery('deals99_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
