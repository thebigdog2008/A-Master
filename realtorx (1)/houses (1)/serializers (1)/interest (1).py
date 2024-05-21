from rest_framework import serializers
from realtorx.houses.models import Interest


class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ("interest", "comment")


class InterestUserSerializer(serializers.ModelSerializer):
    pass


class InterestListSerializer(serializers.ModelSerializer):
    user = InterestUserSerializer()

    class Meta:
        model = Interest
        fields = ("id", "interest", "comment", "user", "created")
