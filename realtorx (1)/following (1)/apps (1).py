from django.apps import AppConfig as BaseAppConfig


class AppConfig(BaseAppConfig):
    name = "realtorx.following"

    def ready(self):
        from realtorx.following import signals  # noqa
