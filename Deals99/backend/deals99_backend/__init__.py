try:
	from .celery import app as celery_app
except Exception:
	# Celery is optional for running the Django development server locally.
	celery_app = None

__all__ = ('celery_app',)
