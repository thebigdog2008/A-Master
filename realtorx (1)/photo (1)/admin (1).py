from django.contrib import admin

from realtorx.photo import models
from realtorx.utils.cms import get_photo_preview


@admin.register(models.Photo)
class PhotoAdmin(admin.ModelAdmin):
    fields = ("image", "width", "height", "added_at")
    readonly_fields = ("added_at",)
    list_display = ("pk", "width", "height", "added_at", "get_photo_preview")

    get_photo_preview = get_photo_preview("image")
