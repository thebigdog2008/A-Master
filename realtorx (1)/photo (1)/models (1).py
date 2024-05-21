from collections import namedtuple

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from hashid_field import HashidAutoField

from realtorx.utils.files import get_random_filename
from realtorx.utils.models import GenericBase

ImageSize = namedtuple("ImageSize", ["width", "height"])


class Photo(GenericBase):
    id = HashidAutoField(primary_key=True)

    image = models.ImageField(
        upload_to=get_random_filename, height_field="height", width_field="width"
    )

    width = models.PositiveSmallIntegerField(blank=True, null=True)
    height = models.PositiveSmallIntegerField(blank=True, null=True)

    added_at = models.DateTimeField(
        _("created at"), editable=False, default=timezone.now
    )

    code = models.CharField(
        verbose_name=_("Code"), max_length=50, null=True, blank=True
    )

    source = models.URLField(
        verbose_name=_("File origin source"), blank=True, max_length=500
    )

    is_main = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("photo")
        verbose_name_plural = _("photos")

    @cached_property
    def admin_url(self):
        app = self._meta.app_label
        model = self._meta.model_name
        return reverse(
            "admin:{app}_{model}_change".format(app=app, model=model), args=(self.id,)
        )

    @property
    def size(self):
        return ImageSize(height=self.height, width=self.width)
