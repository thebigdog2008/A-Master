from rest_framework import serializers

from unicef_restlib.serializers import UserContextSerializerMixin

from realtorx.houses.models import SavedFilter
from realtorx.houses.serializers.house.owned_v2 import StringifiedAmountChoices
from realtorx.utils.serializers.mixins import ModelLevelValidationMixin
from django.core.exceptions import ValidationError
from realtorx.utils.mixpanel import track_mixpanel_event


class SavedFilterSerializer(
    ModelLevelValidationMixin, UserContextSerializerMixin, serializers.ModelSerializer
):
    baths_count_min = serializers.ChoiceField(
        choices=StringifiedAmountChoices.BATHROOMS_AMOUNT, required=False
    )
    carparks_count_min = serializers.ChoiceField(
        choices=StringifiedAmountChoices.CARPARKS_AMOUNT, required=False
    )
    bedrooms_count_min = serializers.ChoiceField(
        choices=StringifiedAmountChoices.BEDROOMS_AMOUNT, required=False
    )

    class Meta:
        model = SavedFilter
        fields = (
            "id",
            "name",
            "action",
            "suburbs",
            "state",
            "county",
            "city",
            "zip_code",
            "house_types",
            "bedrooms_count_min",
            "baths_count_min",
            "carparks_count_min",
            "price_min",
            "price_max",
            "land_size_min",
            "land_size_min_units",
            "internal_land_size_min",
            "internal_land_size_min_units",
            "suitable_for_development",
            "allow_large_dogs",
            "allow_small_dogs",
            "allow_cats",
        )

    def validate(self, attrs):
        attrs["user"] = self.get_user()

        if SavedFilter.objects.filter(user=self.get_user()).count() >= 20:
            raise ValidationError("User should have at most 20 saved filters")

        self.model_level_validation(attrs)
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        track_mixpanel_event(
            str(user.uuid),
            "filter_added",
            {
                "email": user.email,
                "phone": str(user.phone),
                "full_name": user.full_name,
            },
        )
        return super().create(validated_data)
