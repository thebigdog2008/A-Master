from django.apps import AppConfig


class EventAppConfig(AppConfig):
    name = "realtorx.events"

    def ready(self):
        import realtorx.events.signals  # noqa
