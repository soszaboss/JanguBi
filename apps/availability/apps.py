from django.apps import AppConfig


class AvailabilityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.availability'
    
    def ready(self):
        import apps.availability.signals  # noqa
