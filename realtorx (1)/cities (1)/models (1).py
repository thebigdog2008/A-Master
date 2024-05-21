from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from localflavor.us.models import USStateField
from timezone_field import TimeZoneField


class City(models.Model):
    state = USStateField(_("State"))
    county = models.CharField(verbose_name=_("County"), max_length=100)
    name = models.CharField(verbose_name=_("City"), max_length=100)
    zip_codes = ArrayField(models.CharField(max_length=50), verbose_name=_("Zip codes"))
    timezone = TimeZoneField(verbose_name=_("Time zone"))

    class Meta:
        verbose_name_plural = "cities"
        ordering = ["name"]

    def __str__(self):
        return "{state}, {county}, {city}".format(
            state=self.state,
            county=self.county,
            city=self.name,
        )
