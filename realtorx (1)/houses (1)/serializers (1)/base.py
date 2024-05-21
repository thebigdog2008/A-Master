from rest_framework import serializers
from realtorx.houses.models.house import House, HousePhoto
from realtorx.houses.models.interest import Interest
from realtorx.houses.models.saved_filters import SavedFilter
from realtorx.houses.models.incoming_listings import IncomingListing


class BaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = None  # This will be set dynamically
        fields = "__all__"


# List of models to import
all_models = [House, HousePhoto, Interest, SavedFilter, IncomingListing]

# Dynamically add models to the base serializer
for model in all_models:
    serializer_class_name = f"{model.__name__}Serializer"
    serializer_class = type(
        serializer_class_name,
        (BaseSerializer,),
        {"Meta": type("Meta", (), {"model": model, "fields": "__all__"})},
    )
    setattr(BaseSerializer, serializer_class_name, serializer_class)

__all__ = ["BaseSerializer"]
