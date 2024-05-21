from django.contrib.auth import get_user_model

from rest_framework import serializers

from hashid_field.rest import HashidSerializerCharField

from realtorx.houses.models import HousePhoto
from realtorx.photo.models import Photo


class BasePhotoSerializer(serializers.ModelSerializer):
    id = HashidSerializerCharField(source_field="photo.Photo.id", read_only=True)

    class Meta:
        model = Photo
        fields = ["id", "image", "width", "height"]

        _not_required = {"required": False}
        extra_kwargs = {
            "width": _not_required,
            "height": _not_required,
        }


class UserPhotoSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    thumbnail = serializers.ImageField(source="user_photo_thumbnail", read_only=True)
    image = serializers.ImageField(source="photo", allow_null=True)
    width = serializers.ReadOnlyField(source="width_photo", allow_null=True)
    height = serializers.ReadOnlyField(source="height_photo", allow_null=True)

    class Meta:
        model = get_user_model()
        fields = ["id", "image", "thumbnail", "width", "height"]


class HousePhotoSerializer(BasePhotoSerializer):
    thumbnail = serializers.ImageField(source="house_photo_thumbnail", read_only=True)

    class Meta(BasePhotoSerializer.Meta):
        model = HousePhoto
        fields = BasePhotoSerializer.Meta.fields + ["thumbnail"]


class HouseMainPhotoSerializer(BasePhotoSerializer):
    id = serializers.CharField(read_only=True)
    avatar = serializers.ImageField(read_only=True)
    thumbnail = serializers.ImageField(read_only=True)

    class Meta(BasePhotoSerializer.Meta):
        fields = HousePhotoSerializer.Meta.fields + ["avatar", "thumbnail"]
