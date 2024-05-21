from django.apps import AppConfig


class CustomAuthConfig(AppConfig):
    name = "realtorx.custom_auth"
    verbose_name = "Auth"

    def ready(self):
        from realtorx.custom_auth import receivers  # noqa
