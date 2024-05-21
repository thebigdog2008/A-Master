from django.db.models import Q

from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.viewsets import GenericViewSet

from django_filters.rest_framework import DjangoFilterBackend
from requests import HTTPError
from social_core.exceptions import AuthException
from social_django.utils import psa as social_auth_decorator

from realtorx.contact_us.models import Feedback
from realtorx.custom_auth.models import ApplicationUser
from realtorx.custom_auth.serializers import UserAuthSerializer
from realtorx.custom_auth.tasks import (
    send_connection_request_email_to_agent2,
    send_connection_request_email_to_agent3,
)
from realtorx.houses.models import House
from realtorx.registrations.filters import RegistrationFilterSet
from realtorx.registrations.serializers_common import (
    AccessTokenSerializer,
    MakeFollowingListRequestSerializer,
)
from realtorx.sms_backends.view_mixins import SMSVerificationCodeSendCheckViewMixin
from realtorx.utils.permissions import IsEditAction
from datetime import datetime
import pytz
from realtorx.utils.mixpanel import track_mixpanel_event

User = get_user_model()


class RegistrationViewSetBase(
    SMSVerificationCodeSendCheckViewMixin,
    CreateModelMixin,
    ListModelMixin,
    GenericViewSet,
):
    TOKEN_HEADER_NAME = "X-Token"

    queryset = User.objects.all()
    permission_classes = (IsEditAction | IsAuthenticated,)
    filterset_class = RegistrationFilterSet
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["full_name"]

    @action(
        methods=["post"],
        permission_classes=(AllowAny,),
        url_name="check_email_pass",
        url_path="check-email-pass",
        detail=False,
    )
    def check_email_pass(self, *args, **kwargs):
        """
        Check if email and password are valid
        """
        serializer = self.get_serializer(data=self.request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        return Response()

    @action(
        permission_classes=(AllowAny,),
        methods=["post"],
        url_name="check",
        url_path="check",
        detail=False,
    )
    def check_user_registration_data(self, *args, **kwargs):
        serializer = self.get_serializer(data=self.request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        # sms verification code sending
        try:
            self.send_sms_code(serializer.data["phone"])
            return Response()
        except Exception as e:
            return Response({"error": [e.args[2]]})

    @action(
        methods=["post"],
        detail=False,
        permission_classes=[AllowAny],
        url_name="social-auth",
        url_path="(facebook|apple-id|google-oauth2)",
    )
    @method_decorator(social_auth_decorator())
    def social_auth(self, request, backend, *args, **kwargs):
        # token validation
        access_token_serializer = AccessTokenSerializer(
            data=self.request.data,
            context={"request": request, "view": self},
        )
        access_token_serializer.is_valid(raise_exception=True)
        access_token = access_token_serializer.data.get("access_token")

        # authenticate user by social
        try:
            user = request.backend.do_auth(
                access_token,
                user=request.user if request.user.is_authenticated else None,
                user_extra_data=request.data.get("user_extra_data", {}),
            )
        except (HTTPError, AuthException):
            raise ValidationError("Invalid access token")

        if not user:
            raise AuthenticationFailed()

        success_headers = self.get_success_headers(user)
        success_headers.update({self.TOKEN_HEADER_NAME: user.user_auth_tokens.create()})

        return Response(
            data=self.get_serializer(instance=user).data,
            status=status.HTTP_201_CREATED,
            headers=success_headers,
        )

    @action(
        methods=["post"],
        url_name="follow_list_request",
        url_path="follow-list-request",
        detail=False,
    )
    def follow_list_request(self, request, *args, **kwargs):
        contacts_list = request.data.get("contacts_list")
        if not contacts_list:
            return Response(
                "contacts_list parameter should be present",
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = self.get_queryset().filter(uuid__in=contacts_list).only("id").all()
        agent_2_activity_threshold = datetime(2022, 3, 1, tzinfo=pytz.UTC)
        agent_1_email_receiver_count = 0
        agent_2_email_receiver_count = 0
        agent_2_email_skipped_receiver_count = 0
        agent_3_email_receiver_count = 0
        recipient_data = {"email": [], "uuid": [], "agent_type": []}

        # badge can't be present as a list so creation the objects implemented as a cycle for signal triggering in
        # application user
        for recipient in queryset:
            foll_ser = MakeFollowingListRequestSerializer(
                data={"sender": request.user.id, "recipient": recipient.id}
            )

            if not foll_ser.is_valid():
                continue

            recipient_data["email"].append(recipient.email)
            recipient_data["uuid"].append(str(recipient.uuid))
            recipient_data["agent_type"].append(recipient.agent_type)

            track_mixpanel_event(
                str(request.user.uuid),
                "new_connection_request_receiver",
                {
                    "sender_email": request.user.email,
                    "recipient_email": recipient.email,
                    "sender_uuid": str(request.user.uuid),
                    "recipient_uuid": str(recipient.uuid),
                    "sender_agent_type": request.user.agent_type,
                    "recipient_agent_type": recipient.agent_type,
                },
            )

            foll_ser.save()
            if recipient.agent_type == "agent1":
                agent_1_email_receiver_count += 1
            if recipient.agent_type == "agent3":
                send_connection_request_email_to_agent3.delay(
                    request.user.id, recipient.id
                )
                agent_3_email_receiver_count += 1
            elif recipient.agent_type == "agent2":
                if recipient.houses.filter(
                    Q(created__gte=agent_2_activity_threshold)
                    | Q(modified__gte=agent_2_activity_threshold)
                ).exists():
                    send_connection_request_email_to_agent2.delay(
                        request.user.id, recipient.id
                    )
                    agent_2_email_receiver_count += 1
                else:
                    agent_2_email_skipped_receiver_count += 1

        track_mixpanel_event(
            str(request.user.uuid),
            "new_connection_request_sender",
            {
                "sender_email": request.user.email,
                "recipient_email": recipient_data["email"],
                "sender_uuid": str(request.user.uuid),
                "recipient_uuid": recipient_data["uuid"],
                "sender_agent_type": request.user.agent_type,
                "recipient_agent_type": recipient_data["agent_type"],
                "agent_1_recipient_count": agent_1_email_receiver_count,
                "agent_2_recipient_count": agent_2_email_receiver_count,
                "agent_2_recipient_skipped_count": agent_2_email_skipped_receiver_count,
                "agent_3_recipient_count": agent_3_email_receiver_count,
                "case": "multiple connections",
            },
        )

        return Response("Following requests have been sent")

    def get_permissions(self):
        if self.action == "metadata":
            return [AllowAny()]
        return super().get_permissions()

    @action(
        methods=["post"], detail=False, url_path="user-create", url_name="user_create"
    )
    def user_create(self, request, *args, **kwargs):
        phone = request.query_params.get("phone", "")
        count = request.query_params.get("user_count", 10)
        phonenumbers = []
        if count == "":
            count = 10
        if phone != "":
            for i in range(int(count)):
                if not ApplicationUser.objects.filter(phone="+1" + str(phone)).exists():
                    user = ApplicationUser.objects.create_user(
                        full_name="Test " + str(phone) + " User",
                        username="Test_" + str(phone) + "_user",
                        phone="+1" + str(phone),
                        state="NY",
                        city=["Rye"],
                        county=["Westchester"],
                        email="test" + str(phone) + "@yopmail.com",
                        send_email_with_temp_password=True,
                        first_name="Test",
                        last_name="User",
                        agent_type=ApplicationUser.AGENT_TYPE_CHOICES.agent1,
                        temp_password="Test@1234",
                        password="User@1234",
                    )
                    user.save()
                    if user:
                        phonenumbers.append("+1" + str(phone))
                phone = int(phone) + 1
        return Response(phonenumbers)

    @action(
        methods=["post"], detail=False, url_path="user-delete", url_name="user_delete"
    )
    def user_delete(self, request, *args, **kwargs):
        phone = request.query_params.get("phone", "")
        if phone != "":
            phone = phone.split(",")
            for i in phone:
                user = ApplicationUser.objects.filter(phone="+1" + str(i)).first()
                if user:
                    Feedback.objects.filter(user=user).delete()
                    House.objects.filter(user=user).delete()
                    user.delete()
        return Response("Success")


class RegistrationV2ViewSetBase(
    SMSVerificationCodeSendCheckViewMixin,
    CreateModelMixin,
    ListModelMixin,
    GenericViewSet,
):
    TOKEN_HEADER_NAME = "X-Token"

    queryset = User.objects.all()
    permission_classes = (IsEditAction | IsAuthenticated,)
    filterset_class = RegistrationFilterSet
    filter_backends = [DjangoFilterBackend]

    @action(
        permission_classes=(AllowAny,),
        methods=["post"],
        url_name="send_sms",
        url_path="send-sms",
        detail=False,
    )
    def send_sms(self, *args, **kwargs):
        serializer = self.get_serializer(data=self.request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        # sms verification code sending
        try:
            self.send_sms_code(serializer.data["phone"])
            return Response()
        except Exception as e:
            return Response({"error": [e.args[2]]})

    @action(
        methods=["post"],
        permission_classes=(AllowAny,),
        url_name="check_user_data",
        url_path="check-user-data",
        detail=False,
    )
    def check_user_data(self, *args, **kwargs):
        serializer = self.get_serializer(data=self.request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        # sms verification code sending
        try:
            self.send_sms_code(serializer.data["phone"])
            return Response()
        except Exception as e:
            return Response({"error": [e.args[2]]})

    def create(self, request, *args, **kwargs):
        import logging

        logger = logging.getLogger("django.list_hub")
        response = super(RegistrationV2ViewSetBase, self).create(
            request, *args, **kwargs
        )

        serializer = UserAuthSerializer(data=request.data)
        logger.error("\nUserAuthSerializer serializer response - {}".format(serializer))
        serializer.is_valid(raise_exception=True)
        user = serializer.authenticate()
        logger.error("\nnewly created user authentication - {}".format(user))
        return Response(
            data=response.data,
            status=status.HTTP_201_CREATED,
            headers=self.get_token_headers(user),
        )

    @classmethod
    def get_token_headers(cls, user):
        return {cls.TOKEN_HEADER_NAME: user.user_auth_tokens.create()}


class RegistrationV3ViewSetBase(
    SMSVerificationCodeSendCheckViewMixin,
    CreateModelMixin,
    ListModelMixin,
    GenericViewSet,
):
    TOKEN_HEADER_NAME = "X-Token"

    queryset = User.objects.all()
    permission_classes = (IsEditAction | IsAuthenticated,)
    filterset_class = RegistrationFilterSet
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["full_name"]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        connected_queryset = queryset.filter(following__id__in=[self.request.user.id])
        connected_connections = self.get_serializer(connected_queryset, many=True)
        in_follow = list(
            self.request.user.in_coming_requests.filter(
                sender__id__in=queryset.values_list("id", flat=True), status="pending"
            ).values_list("sender__id", flat=True)
        )
        out_follow = in_follow + list(
            self.request.user.out_coming_requests.filter(
                recipient__id__in=queryset.values_list("id", flat=True),
                status="pending",
            ).values_list("recipient__id", flat=True)
        )

        new_queryset = queryset.exclude(id__in=out_follow).exclude(
            id__in=connected_queryset.values_list("id", flat=True)
        )
        new_connections = self.get_serializer(new_queryset, many=True)

        return Response(
            {
                "connected_connections": connected_connections.data,
                "new_connections": new_connections.data,
            }
        )
