from django.utils.translation import gettext_lazy as _

from model_utils import Choices

LAND_UNITS = Choices(
    ("sqft", _("ft²")),  # Square feets
    ("sqmt", _("m²")),  # Square meters
    ("acre", _("ac")),  # Acres
    ("hect", _("ha")),  # Hectares
)

_land_size_units_to_m2 = {
    LAND_UNITS.sqft: 0.09290304,
    LAND_UNITS.sqmt: 1,
    LAND_UNITS.acre: 4046.86,
    LAND_UNITS.hect: 10000,
}


def get_land_size_in_m2(value, units):
    if not value or not units or units not in _land_size_units_to_m2:
        return None
    return value * _land_size_units_to_m2[units]
