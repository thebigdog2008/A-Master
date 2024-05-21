import json

from django.contrib.gis.geos import GEOSGeometry
from django.utils.translation import gettext as _

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Field


class GeoPointField(Field):
    def to_representation(self, value):
        point_json = json.loads(value.json)
        point_coordinates = point_json["coordinates"]

        point = {"lng": point_coordinates[0], "ltd": point_coordinates[1]}

        return point

    def to_internal_value(self, point):
        if "lng" not in point or "ltd" not in point:
            raise ValidationError(
                _("Format of `point` should be `{'lng': 20.0, 'ltd': 20.0}`")
            )

        point = GEOSGeometry(
            "POINT({lng} {ltd})".format(lng=point["lng"], ltd=point["ltd"])
        )

        return point


class WhiteListField(serializers.RelatedField):
    serializer = None

    def __init__(self, **kwargs):
        self.serializer = kwargs.pop("serializer", self.serializer)
        super(WhiteListField, self).__init__(**kwargs)

    def to_representation(self, value):
        data = self.serializer(value).data
        return data

    def to_internal_value(self, data):
        user = self.queryset.get(uuid=data)
        return user
