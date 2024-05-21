import logging

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry

import googlemaps
from django.core.exceptions import ValidationError

from realtorx.utils.address import parse_address

global place_id


def get_point_from_address(address: str) -> GEOSGeometry:
    """
    Fetch a point from google geocode result by specified address
    """
    point = None
    api_key = settings.MAP_WIDGETS["GOOGLE_MAP_API_KEY"]
    global place_id
    try:
        gmaps = googlemaps.Client(key=api_key)
        geocode_result = googlemaps.client.geocode(gmaps, address=address)
        place_id = geocode_result[0]["place_id"]
        point = (
            GEOSGeometry(
                "POINT({0} {1})".format(
                    geocode_result[0]["geometry"]["location"]["lng"],
                    geocode_result[0]["geometry"]["location"]["lat"],
                )
            )
            if geocode_result
            else None
        )
    except ValueError:
        if not api_key:
            logging.error("GOOGLE_API_KEY not set.")
        else:
            logging.error("GOOGLE_API_KEY rejected by the server.")
    return point


def get_address_from_point(point: GEOSGeometry) -> list:
    """
    Fetch an address from google geocode result by point
    """
    address = None
    api_key = settings.MAP_WIDGETS["GOOGLE_MAP_API_KEY"]
    global place_id
    try:
        gmaps = googlemaps.Client(key=api_key)
        geocode_result = googlemaps.client.reverse_geocode(gmaps, (point[1], point[0]))
        address = parse_address(geocode_result)
        place_data = gmaps.reverse_geocode(place_id)
        street_number = place_data[0]["address_components"][0]["long_name"]
        street_address = place_data[0]["address_components"][1]["long_name"]
        address = list(address)
        address[0] = street_number
        address[1] = street_address
        address = tuple(address)
    except ValueError:
        if not api_key:
            logging.error("GOOGLE_API_KEY not set.")
        else:
            logging.error("GOOGLE_API_KEY rejected by the server.")
    return address


def validate_file_size(value):
    # calculate the video upload file size not more than 20MB
    filesize = value.size

    if filesize > 20971520:
        raise ValidationError(
            f"The maximum video file size that can be uploaded is 20MB. "
            f"Selected file size is {'%.1f' % float(filesize / 1000000) + 'MB'}"
        )
    else:
        return value
