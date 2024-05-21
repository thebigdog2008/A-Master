import itertools

from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe


@mark_safe
def build_changelist_link(app_name, lookup, value, as_button=False):
    if value == 0:
        return "0"

    urlconf = getattr(settings, "CMS_URLCONF", None)
    reference = reverse(f"admin:{app_name}_changelist", urlconf)
    class_attr = "button" if as_button else ""

    return f'<a target="_blank" class="{class_attr}" href="{reference}?{lookup}">{value}</a>'


def get_photo_preview(field_name, max_width=100, max_height=100):
    def photo_preview(self, obj):
        image = getattr(obj, field_name)
        if not image:
            return ""

        return mark_safe(  # noqa
            (
                '<a href="{url}" target="_blank">'
                '<img src="{url}" style="max-height: {height}px; max-width: {width}px;">'
                "</a>"
            ).format(url=image.url, width=max_width, height=max_height)
        )

    photo_preview.short_description = "{field_name} Preview".format(
        field_name=field_name.title()
    )

    return photo_preview


def complete_fieldsets(fieldsets, model, exclude=()):
    fields = map(
        lambda x: x.name,
        filter(lambda x: x.editable and not x.auto_created, model._meta.fields),
    )
    fields_in_use = itertools.chain.from_iterable(
        map(lambda x: x[1]["fields"], fieldsets)
    )
    missing_fields = set(fields) - set(fields_in_use) - set(exclude)
    if missing_fields:
        fieldsets = list(fieldsets)
        fieldsets.append(
            (
                "Extra",
                {
                    "fields": tuple(missing_fields),
                },
            )
        )
    return tuple(fieldsets)
