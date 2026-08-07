from django.apps import AppConfig


class ProgressConfig(AppConfig):
    name = 'progress'

    def ready(self):
        import progress.signals 