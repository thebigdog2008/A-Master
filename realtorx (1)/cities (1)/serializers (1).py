from rest_framework import serializers

from realtorx.cities.models import City


class CitySerializer(serializers.ModelSerializer):
    value = serializers.CharField(source="name")
    display_name = serializers.CharField(source="name")

    class Meta:
        model = City
        fields = ("value", "display_name", "zip_codes")


class CountySerializer(serializers.ModelSerializer):
    value = serializers.CharField(source="county")
    display_name = serializers.CharField(source="county")

    class Meta:
        model = City
        fields = ("value", "display_name")
