from django.contrib.auth import get_user_model
from rest_framework import mixins, viewsets, permissions
from realtorx.houses.models.saved_filters import SavedFilter
from realtorx.custom_auth.models import ApplicationUser

from realtorx.registrations.serializers import (
    RegistrationSerializer,
    RegistrationSerializerV2,
    RegistrationSerializerV3,
    RegistrationSerializerV4,
    TrialUserSerializer,
)
from realtorx.registrations.serializers_common import (
    CheckEmailPass,
    CheckPhoneData,
    CheckProfileData,
    CheckUserDataSerializer,
)
from realtorx.registrations.views_base import (
    RegistrationV2ViewSetBase,
    RegistrationViewSetBase,
    RegistrationV3ViewSetBase,
)
from rest_framework.response import Response
from django.conf import settings

User = get_user_model()


class RegistrationViewSet(RegistrationViewSetBase):
    serializer_class = RegistrationSerializer

    def get_serializer_class(self):
        if self.action == "check_email_pass":
            return CheckEmailPass
        elif self.action == "check_user_registration_data":
            return CheckProfileData
        return super().get_serializer_class()


class RegistrationV2ViewSet(RegistrationV2ViewSetBase):
    serializer_class = RegistrationSerializerV2

    def get_serializer_class(self):
        if self.action == "send_sms":
            return CheckPhoneData
        if self.action == "check_user_data":
            return CheckUserDataSerializer
        return super().get_serializer_class()


class RegistrationV3ViewSet(RegistrationV3ViewSetBase):
    serializer_class = RegistrationSerializerV3

    def get_serializer_class(self):
        if self.action == "check_email_pass":
            return CheckEmailPass
        elif self.action == "check_user_registration_data":
            return CheckProfileData
        return super().get_serializer_class()


class RegistrationV4ViewSet(RegistrationViewSetBase):
    serializer_class = RegistrationSerializerV4


class TrialUserViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ApplicationUser.objects.all()
    serializer_class = TrialUserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            data = TrialUserSerializer(user).data
            token = user.user_auth_tokens.create().key
            # data['token'] = token
            SavedFilter.objects.create(
                user=user,
                name=SavedFilter.DEFAULT_FILTER_NAME,
                action="sell",
                price_min=0,
                price_max=settings.FILTER_MAX_PRICE,
                baths_count_min=0.0,
                state="CA",
                carparks_count_min=0,
                bedrooms_count_min=0,
                house_types=[
                    "House",
                    "Townhouse",
                    "Apartments",
                    "CondosCo-Ops",
                    "Lotsland",
                ],
            )
            return Response(data=data, headers={"x-token": token}, status=201)
        return Response(serializer.errors, status=400)

    def post(self, request, *args, **kwargs):
        return self.create(self, request, *args, **kwargs)
