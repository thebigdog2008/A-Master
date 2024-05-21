from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext as _

from rest_framework.serializers import CharField, ImageField, ModelSerializer
from rest_framework.validators import UniqueValidator

from phonenumber_field.serializerfields import PhoneNumberField

User = get_user_model()


class RegistrationSerializerBase(ModelSerializer):
    phone = PhoneNumberField(
        required=True,
        validators=[
            UniqueValidator(
                User.objects.all(),
                message=_("This number already exists on a user account"),
            ),
        ],
    )
    avatar_thumbnail_square = ImageField(read_only=True)
    agency_name = CharField(source="agency.name", allow_null=True)

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "full_name",
            "email",
            "state",
            "phone",
            "password",
            "uuid",
            "avatar_thumbnail_square",
            "agency_name",
        )
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
            "full_name": {"required": False},
            "password": {"write_only": True, "validators": [validate_password]},
            "email": {
                "validators": [UniqueValidator(User.objects.all(), lookup="iexact")]
            },
        }
        read_only_fields = ("uuid",)

    def save(self, **kwargs):
        password = self.validated_data.pop("password", None)

        user = super().save(**kwargs)
        if password:
            user.set_password(password)
            user.save(update_fields=["password"])

        return user


class RegistrationSerializerBaseV2(ModelSerializer):
    phone = PhoneNumberField(
        required=True,
        validators=[
            UniqueValidator(
                User.objects.all(),
                message=_("This number already exists on a user account"),
            ),
        ],
    )

    class Meta:
        model = User
        fields = ("phone", "password", "uuid")
        extra_kwargs = {
            "first_name": {"required": False},
            "last_name": {"required": False},
            "full_name": {"required": False},
            "password": {"write_only": True, "validators": [validate_password]},
        }
        read_only_fields = ("uuid",)

    def save(self, **kwargs):
        password = self.validated_data.pop("password", None)

        user = super().save(**kwargs)
        if password:
            user.set_password(password)
            user.save(update_fields=["password"])

        return user
