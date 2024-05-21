from django.db import models
from realtorx.agencies.models import AgencyBranch
from model_utils import Choices
from django.utils.translation import gettext_lazy as _
from realtorx.photo.image_specs import SquareThumbnailSpec, ThumbnailSpec
from localflavor.us.models import USStateField
from imagekit.models import ImageSpecField
import random


class BongoLicence(models.Model):
    TYPE_CHOICES = Choices(
        ("agent", _("Agent")),
        ("associate_broker", _("Associate Broker")),
        ("broker", _("Broker")),
        ("unlicensed", _("Unlicensed")),
    )

    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default="unlicensed")


    user = models.ForeignKey(
        "ApplicationUser",
        verbose_name=_("Agent"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name=("licences")
    )

    state = USStateField(_("State"))
    bongo_license = models.BooleanField(default=False)
    bongo_license_id = models.CharField(
        verbose_name=_("Licence id"), max_length=200, unique=True)
    bongo_500_license = models.BooleanField(default=False)
    type = models.CharField(
        verbose_name=_("Licence Type"),
        max_length=200,
        choices=TYPE_CHOICES,
        default=TYPE_CHOICES.agent,
    )

    class Meta:
        verbose_name = _("Bongo licence")

    def assign_bongo_license_id(self):
        self.bongo_license_id = f"{self.state}-{str(random.randint(1001, 20000))}"

class StripePaymentHistory(models.Model):
    user = models.ForeignKey(
        "ApplicationUser",
        verbose_name=_("user"),
        on_delete=models.CASCADE,
        related_name="stripe_payments",
    )


class Agent(models.Model):
    email = models.ForeignKey(null=True, blank=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    key = models.CharField(max_length=255, null=True, blank=True)
    mls_id = models.CharField(max_length=255)
    preferred_phone = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    bongo_license_id = models.CharField(max_length=255, null=True, blank=True)
    bongo_license = models.BooleanField(default=False)
    bongo_500 = models.BooleanField(default=False)
    active_listings = models.SmallIntegerField(max_length=6, null=True, blank=True)
    avatar = models.ImageField(verbose_name=_("Avatar"), blank=True)
    avatar_thumbnail_square = ImageSpecField(source="avatar", spec=SquareThumbnailSpec)
    url = models.URLField(max_length=255, null=True, blank=True)

    agency_branch = models.ForeignKey(
        "AgencyBranch",
        related_name="agents",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.full_name

    def houses_count(self):
        return self.houses.count()

    class Meta:
        verbose_name_plural = "Agents"
        ordering = [
            "id",
        ]
