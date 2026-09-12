from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core / Accounts'

    def ready(self):
        # Import signal handlers to ensure audit logging is active
        try:
            from . import signals  # noqa: F401
        except Exception:
            # Avoid crashing app import if signals fail
            pass
