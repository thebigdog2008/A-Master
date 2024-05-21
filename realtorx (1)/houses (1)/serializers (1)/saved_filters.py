from rest_framework import serializers

from unicef_restlib.serializers import UserContextSerializerMixin

from realtorx.houses.models import SavedFilter
from realtorx.houses.serializers.house.owned import OriginalAmountChoices
from realtorx.utils.serializers.mixins import ModelLevelValidationMixin


class SavedFilterSerializer(
    ModelLevelValidationMixin, UserContextSerializerMixin, serializers.ModelSerializer
):
    baths_count_min = serializers.ChoiceField(
        choices=OriginalAmountChoices.BATHROOMS_AMOUNT, required=False
    )
    carparks_count_min = serializers.ChoiceField(
        choices=OriginalAmountChoices.CARPARKS_AMOUNT, required=False
    )
    bedrooms_count_min = serializers.ChoiceField(
        choices=OriginalAmountChoices.BEDROOMS_AMOUNT, required=False
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
        )

    def validate(self, attrs):
        attrs["user"] = self.get_user()

        self.model_level_validation(attrs)
        return attrs
