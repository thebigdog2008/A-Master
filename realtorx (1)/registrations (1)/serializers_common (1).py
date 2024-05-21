from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext as _

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    CharField,
    ChoiceField,
    EmailField,
    ModelSerializer,
    Serializer,
)
from rest_framework.validators import UniqueValidator

from localflavor.us.us_states import STATE_CHOICES
from phonenumber_field.serializerfields import PhoneNumberField

from realtorx.custom_auth.models import ApplicationUser
from realtorx.following.models import FollowingRequest
from realtorx.utils.serializers.mixins import ModelLevelValidationMixin


class AccessTokenSerializer(Serializer):
    access_token = CharField(max_length=1024)


class CheckEmailPass(Serializer):
    email = EmailField(
        validators=[UniqueValidator(ApplicationUser.objects.all(), lookup="iexact")]
    )
    password = CharField(write_only=True, validators=[validate_password])


class CheckProfileData(Serializer):
    first_name = CharField()
    last_name = CharField()
    full_name = CharField(required=False)
    state = ChoiceField(choices=STATE_CHOICES, required=False)
    agency_name = CharField(required=False)
    phone = PhoneNumberField(
        validators=[
            UniqueValidator(
                ApplicationUser.objects.all(),
                message=_("This number already exists on a user account"),
            ),
        ]
    )


class MakeFollowingListRequestSerializer(ModelLevelValidationMixin, ModelSerializer):
    class Meta:
        model = FollowingRequest
        fields = ("sender", "recipient")

    def validate(self, attrs):
        self.model_level_validation(attrs)
        return attrs


class CheckPhoneData(Serializer):
    phone = PhoneNumberField(required=True)


class CheckUserDataSerializer(Serializer):
    phone = PhoneNumberField()
    password = CharField(write_only=True, validators=[validate_password])

    def validate(self, attrs):
        attrs = super().validate(attrs)
        phone = attrs.get("phone", None)
        user = ApplicationUser.objects.filter(phone=phone)
        if user.exists():
            raise ValidationError(
                f"Hi {user[0].first_name},\nYou have already had an account automatically created for you, to reset "
                f"your password please click below and follow the prompts."
            )
        return attrs

    # def validate(self, attrs):
    #     attrs = super().validate(attrs)
    #     phone = attrs.get('phone', None)
    #     user = ApplicationUser.objects.filter(phone=phone)
    #     if user.exists():
    #         user = user.first()
    #         if user.send_email_with_temp_password:
    #             raise ValidationError(
    #                 f"Hi, {user.first_name}\nYou have already had an account automatically created for you, to reset "
    #                 f"your password please click below and follow the prompts.")
    #         raise ValidationError({'phone': ['An account already exists with this phone number']})

    #         # if ApplicationUser.objects.filter(phone=phone, send_email_with_temp_password=True).exists():
    #         #     user = ApplicationUser.objects.filter(phone=phone, send_email_with_temp_password=True).first()
    #         #     if user.password == '':
    #         #         user.set_password(user.temp_password)
    #         #         user.save()
    #         #     # send_templated_mail(
    #         #     #     template_name='login_and_temp_password',
    #         #     #     from_email=settings.DEFAULT_FROM_EMAIL,
    #         #     #     recipient_list=[
    #         #     #         user.email,
    #         #     #     ],
    #         #     #     context={
    #         #     #         'user_fullname': user.full_name,
    #         #     #         'user_phone': str(user.phone),
    #         #     #         'user_temp_password': user.temp_password,
    #         #     #     },
    #         #     # )
    #         #     # raise ValidationError(err_text)
    #         #     raise ValidationError(
    #         #         f"Hi, {user.first_name}\nYou have already had an account automatically created for you, to reset "
    #         #         f"your password please click below and follow the prompts.")
    #         # raise ValidationError(_('An account already exists with this phone number'))
    #     return attrs
