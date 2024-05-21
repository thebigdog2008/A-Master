from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _

from realtorx.utils.files import get_document_path
from realtorx.utils.models import GenericBase


class Attachment(GenericBase):
    file = models.FileField(upload_to=get_document_path)

    added_at = models.DateTimeField(
        _("Created at"), editable=False, default=timezone.now
    )

    source = models.URLField(verbose_name=_("File origin source"), blank=True)

    class Meta:
        verbose_name = _("File")
        verbose_name_plural = _("Files")
