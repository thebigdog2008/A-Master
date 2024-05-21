from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


class GenericBase(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        blank=True,
        null=True,
        verbose_name=_("Content Type"),
        related_name="+",
        on_delete=models.CASCADE,
    )
    object_id = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=_("Object ID"),
    )
    content_object = GenericForeignKey()

    class Meta:
        abstract = True
