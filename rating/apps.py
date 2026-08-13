from django.apps import AppConfig


class RatingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rating'

    def ready(self):
        import rating.signals  # noqa: F401