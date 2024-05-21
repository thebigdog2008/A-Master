from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

from rest_framework.relations import RelatedField


class LookupRelatedField(RelatedField):
    default_error_messages = {
        "required": _("This field is required."),
        "does_not_exist": _('Invalid lookup "{value}" - object does not exist.'),
        "incorrect_type": _("Incorrect type."),
    }

    def __init__(self, **kwargs):
        self.lookup_field = kwargs.pop("lookup_field", None)
        assert (
            self.lookup_field is not None
        ), "The `lookup_field` argument is required."  # NOQA: S101
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            return self.get_queryset().get(**{self.lookup_field: data})
        except ObjectDoesNotExist:
            self.fail("does_not_exist", value=data)
        except (TypeError, ValueError):
            self.fail("incorrect_type")

    def to_representation(self, value):
        return getattr(value, self.lookup_field)
