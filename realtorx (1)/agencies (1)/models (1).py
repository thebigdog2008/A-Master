# models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from realtorx.utils.files import get_agency_logo_path
from localflavor.us.models import USStateField
from phonenumber_field.modelfields import PhoneNumberField
from django_fsm import FSMIntegerField


class Agency(models.Model):
    name = models.CharField(verbose_name=_("Agency name"), max_length=200)
    about = models.TextField(verbose_name=_("About agency"), blank=True)
    agency_logo = models.ImageField(
        upload_to=get_agency_logo_path, null=True, blank=True
    )
    listhub_validation = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Agencies"

    def __str__(self):
        return self.name


class AgencyBranch(models.Model):
    List_office_name = models.CharField(
        verbose_name=_("List office name"),
        max_length=200,
        null=True,
        blank=True,
        default=None,
    )
    list_office_address1 = models.CharField(
        verbose_name=_("Agency address"), max_length=1024, null=True, blank=True
    )
    list_office_city = models.CharField(max_length=100, null=True, blank=True)
    list_office_state = USStateField(_("State"), null=True, blank=True)
    list_office_postal_code = models.CharField(
        verbose_name=_("Agency Zip Code"), max_length=32, null=True, blank=True
    )
    agency = models.ForeignKey(
        Agency,
        null=True,
        blank=True,
        related_name="agency",
        on_delete=models.DO_NOTHING,
    )
    list_office_phone = PhoneNumberField(
        verbose_name=_("Branch phone number"), null=True, blank=True
    )
    created_from_listhub = models.BooleanField(default=True)
    sql_validation = models.BooleanField(default=False)
    sql_state = FSMIntegerField(default=0, verbose_name=_("SQL_State"))

    class Meta:
        verbose_name_plural = "Agency Branch"

    def __str__(self):
        return "{city}, {state}".format(
            city=self.city,
            state=self.state,
        )

    def save(self, *args, **kwargs):
        if self.list_office_phone and not str(self.list_office_phone).startswith("+1"):
            self.list_office_phone = "+1" + str(self.list_office_phone)
        super().save(*args, **kwargs)
