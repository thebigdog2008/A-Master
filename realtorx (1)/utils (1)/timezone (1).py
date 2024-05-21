from django.utils.functional import SimpleLazyObject

from timezonefinder import TimezoneFinder

tz_finder = SimpleLazyObject(lambda: TimezoneFinder(in_memory=True))


def get_timezone_by_coordinates(latitude, longitude):
    timezone = tz_finder.timezone_at(lat=latitude, lng=longitude)
    if timezone:
        timezone = tz_finder.closest_timezone_at(lat=latitude, lng=longitude)

    return timezone
