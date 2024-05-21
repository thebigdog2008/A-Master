from django.apps import AppConfig


class AgenciesConfig(AppConfig):
    name = "realtorx.agencies"

    def ready(self):
        from realtorx.agencies import signals  # noqa
