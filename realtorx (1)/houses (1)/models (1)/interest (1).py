from django.conf import settings
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from realtorx.houses.models.house import House


class Interest(TimeStampedModel):
    INTEREST_NO = 1
    INTEREST_YES = 2

    INTEREST_STATE = (
        (INTEREST_NO, _("No")),
        (INTEREST_YES, _("Yes")),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="interests",
        on_delete=models.CASCADE,
        verbose_name=_("User"),
    )
    house = models.ForeignKey(
        House,
        related_name="interests",
        on_delete=models.CASCADE,
        verbose_name=_("House"),
    )

    comment = models.TextField(verbose_name=_("Comment"), blank=True)

    interest = models.SmallIntegerField(
        verbose_name=_("Interest in a house"),
        choices=INTEREST_STATE,
    )
    system_generated = models.BooleanField(
        default=False
    )  # Just a flag to denote that interest from steves account was through task/script

    class Meta:
        ordering = ["id"]
        verbose_name = _("Interest")

    def __str__(self):
        return "{interest} {address}".format(
            interest=self.interest, address=self.house.unparsed_address
        )
