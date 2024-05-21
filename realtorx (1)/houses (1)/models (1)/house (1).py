from django.db import models

from realtorx.utils.files import get_document_path
from realtorx.utils.models import GenericBase


class House(models.Model):
    odata_id = models.URLField(max_length=255, null=True, blank=True)
    house_key = models.CharField(max_length=255, null=True, blank=True)
    modification_timestamp = models.DateTimeField(null=True, blank=True)
    house_id = models.CharField(max_length=255)
    property_type = models.CharField(max_length=255, null=True, blank=True)
    property_sub_type = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unparsed_address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    postal_code = models.CharField(max_length=255, null=True, blank=True)
    baths_count = models.IntegerField(null=True, blank=True)
    bedroom_count = models.IntegerField(null=True, blank=True)
    carparks_count = models.IntegerField(null=True, blank=True)
    standard_status = models.CharField(max_length=255, null=True, blank=True)
    lot_size = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    lot_size_units = models.CharField(max_length=255, null=True, blank=True)
    lot_size_area = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    living_area = models.IntegerField(null=True, blank=True)
    living_area_units = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    disclaimer = models.TextField(null=True, blank=True)
    public_remarks = models.TextField(null=True, blank=True)
    photos_count = models.IntegerField(null=True, blank=True)
    photos_change_timestamp = models.DateTimeField(null=True, blank=True)
    source_system_id = models.CharField(max_length=255, null=True, blank=True)
    year_built = models.IntegerField(null=True, blank=True)
    year_built_effective = models.IntegerField(null=True, blank=True)
    house_contract_date = models.DateField(null=True, blank=True)
    franchise_affiliation = models.CharField(max_length=255, null=True, blank=True)

    agent = models.ForeignKey(
        "Agent", related_name="houses", on_delete=models.SET_NULL, null=True, blank=True
    )

    source = models.ForeignKey(
        "IncomingListing",
        related_name="house",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    interested_users = models.ManyToManyField("bongo.User", blank=True)

    def __str__(self):
        return self.house_id

    class Meta:
        ordering = ["id"]


class HousePhoto(models.Model):
    key = models.CharField(max_length=255, verbose_name="Media Key")
    url = models.URLField(null=True, blank=True, verbose_name="Media URL")
    modification_timestamp = models.DateTimeField(
        null=True, blank=True, verbose_name="Modification Timestamp"
    )
    short_description = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Short Description"
    )
    long_description = models.TextField(
        null=True, blank=True, verbose_name="Long Description"
    )

    property_house = models.ForeignKey(
        "House", related_name="photos", on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"Photo - {self.key}"

    class Meta:
        verbose_name_plural = "Listing Photos"
        ordering = ["id"]


class HousePhoto(models.Model):
    key = models.CharField(max_length=255, verbose_name="Media Key")
    url = models.URLField(null=True, blank=True, verbose_name="Media URL")
    modification_timestamp = models.DateTimeField(
        null=True, blank=True, verbose_name="Modification Timestamp"
    )
    short_description = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Short Description"
    )
    long_description = models.TextField(
        null=True, blank=True, verbose_name="Long Description"
    )

    property_listing = models.ForeignKey(
        "House", related_name="photos", on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"Photo - {self.key}"

    class Meta:
        verbose_name_plural = "Listing Photos"
        ordering = ["id"]


class Attachment(GenericBase):
    file = models.FileField(upload_to=get_document_path)

    added_at = models.DateTimeField(
        _("Created at"), editable=False, default=timezone.now
    )

    source = models.URLField(verbose_name=_("File origin source"), blank=True)

    class Meta:
        verbose_name = _("File")
        verbose_name_plural = _("Files")
