from rest_framework import serializers
from realtorx.custom_auth.models import ApplicationUser, BrokerLicence


class ApplicationUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationUser
        fields = "__all__"


class BrokerLicenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrokerLicence
        fields = "__all__"
