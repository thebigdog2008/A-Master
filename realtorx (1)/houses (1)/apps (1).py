from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class HousesAppConfig(AppConfig):
    name = "realtorx.houses"
    verbose_name = _("Houses")
    label = "houses"

    def ready(self):
        from realtorx.houses import signals  # noqa
