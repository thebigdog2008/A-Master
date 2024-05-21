from rest_framework import serializers
from .models import Agency, AgencyBranch


class AgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Agency
        fields = ("id", "name", "about", "agency_logo")


class AgencyAddressSerializer(serializers.ModelSerializer):
    agency_address = serializers.SerializerMethodField()

    class Meta:
        model = AgencyBranch
        fields = (
            "id",
            "list_office_address1",
            "list_office_postal_code",
            "list_office_city",
            "list_office_state",
            "agency",
        )

    def get_agency_address(self, obj):
        address = obj.list_office_address1 if obj.list_office_address1 else ""
        list_office_city = obj.list_office_city if obj.list_office_city else ""
        list_office_state = obj.list_office_state if obj.list_office_state else ""
        agency_address = f"{address}, {list_office_city}, {list_office_state}," ""
        return agency_address.strip(", ")
