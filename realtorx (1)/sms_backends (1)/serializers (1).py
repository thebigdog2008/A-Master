from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import CharField, Serializer

from phonenumber_field.serializerfields import PhoneNumberField
from twilio.base.exceptions import TwilioRestException

User = get_user_model()


class SMSVerificationSerializer(Serializer):
    code = CharField()
    to = PhoneNumberField()

    def validate(self, attrs):
        # check sms code. raise validation error if "code" invalid
        try:
            response = self.context["view"].sms_backend_obj.check_verify(
                attrs["to"].as_international, attrs["code"]
            )
        except TwilioRestException as ex:
            raise ValidationError(ex)

        if not response.status == "approved":
            raise ValidationError(_("The code not approved"))
        return attrs


class SMSResetCodeSerializer(Serializer):
    code = CharField()
    to = PhoneNumberField()

    def validate(self, attrs):
        # check sms code. raise validation error if "code" invalid
        try:
            response = self.context["view"].sms_backend_obj.check_verify(
                attrs["to"].as_international, attrs["code"]
            )
        except TwilioRestException as ex:
            raise ValidationError(ex)

        if not response.status == "approved":
            raise ValidationError(_("The code not approved"))
        return attrs
