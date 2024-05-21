from django.db import models


class IncomingListing(models.Model):
    json = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    errors = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Incoming Listings"
        ordering = [
            "id",
        ]
