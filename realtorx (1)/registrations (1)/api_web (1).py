from realtorx.registrations.serializers_common import CheckEmailPass, CheckProfileData
from realtorx.registrations.serializers_web import RegistrationSerializer
from realtorx.registrations.views_base import RegistrationViewSetBase


class RegistrationViewSet(RegistrationViewSetBase):
    serializer_class = RegistrationSerializer

    def get_serializer_class(self):
        if self.action == "check_email_pass":
            return CheckEmailPass
        elif self.action == "check_user_registration_data":
            return CheckProfileData
        return super().get_serializer_class()
