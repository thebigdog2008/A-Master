from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class RateLimit(models.Model):
    key = models.CharField(max_length=256)
    value = models.CharField(max_length=256)

    class Meta:
        verbose_name_plural = "Rate-limit"

    def __str__(self):
        return f"{self.key} - {self.value}"

    def clean(self):
        if (
            not self.id
            and self.__class__.objects.filter(
                key=self.key,
            ).exists()
        ):
            raise ValidationError(_("This rate limit already exists."))


class KeyValue(models.Model):
    key = models.CharField(max_length=256)
    value = models.CharField(max_length=256)

    class Meta:
        verbose_name_plural = "Key-Value"

    def __str__(self):
        return f"{self.key} - {self.value}"

    def clean(self):
        if (
            not self.id
            and self.__class__.objects.filter(
                key=self.key,
            ).exists()
        ):
            raise ValidationError(_("This key already exists."))
