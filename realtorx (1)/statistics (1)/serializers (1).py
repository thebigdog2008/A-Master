from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework import serializers

from drf_extra_fields.fields import DateTimeRangeField
from unicef_restlib.fields import SeparatedReadWriteField
from unicef_restlib.serializers import UserContextSerializerMixin

from realtorx.appointments.models import UserAppointment
from realtorx.appointments.serializers import AppointmentHouseSerializer
from realtorx.house_chats.models import Chat
from realtorx.house_chats.serializers.chats import ChatHouseSerializer
from realtorx.houses.models import House
from realtorx.houses.models.interest import Interest
from datetime import datetime, timedelta, time
import pytz

User = get_user_model()


class StatisticSerializer(serializers.Serializer):
    sent_to = serializers.IntegerField(source="sent_to_count", read_only=True)
    interested = serializers.IntegerField(read_only=True)
    not_interested = serializers.IntegerField(read_only=True)
    no_response = serializers.SerializerMethodField()
    messages = serializers.IntegerField(read_only=True)
    upcoming_appointments = serializers.IntegerField(read_only=True)

    def get_no_response(self, obj):
        interested_count = Interest.objects.filter(
            house_id=obj.id,
            interest=Interest.INTEREST_YES,
        ).count()
        not_interested_count = Interest.objects.filter(
            house_id=obj.id,
            interest=Interest.INTEREST_NO,
        ).count()
        return obj.sent_to_count - interested_count - not_interested_count


class UserStatisticWebSerializerMixin(serializers.ModelSerializer):
    avatar = serializers.ImageField(source="avatar_thumbnail_square", read_only=True)

    class Meta:
        model = User
        fields = ("full_name", "email", "avatar", "phone")


class UserStatisticWebSerializer(UserStatisticWebSerializerMixin):
    pass


class UpcomingAppointmentsStatisticSenderWebSerializer(UserStatisticWebSerializerMixin):
    pass


class UpcomingAppointmentsStatisticWebSerializer(serializers.ModelSerializer):
    sender = UpcomingAppointmentsStatisticSenderWebSerializer(read_only=True)

    class Meta:
        model = UserAppointment
        fields = ("scheduled_date", "sender")


class MessagesStatisticRecipientWebSerializer(UserStatisticWebSerializerMixin):
    pass


class MessagesStatisticWebSerializer(
    UserContextSerializerMixin, serializers.ModelSerializer
):
    creator = UserStatisticWebSerializer(read_only=True)
    recipient = MessagesStatisticRecipientWebSerializer(read_only=True)

    class Meta:
        model = Chat
        fields = ("creator", "recipient", "last_message_at")


class InterestedStatisticUserWebSerializer(UserStatisticWebSerializerMixin):
    pass


class InterestedStatisticWebSerializer(serializers.ModelSerializer):
    user = InterestedStatisticUserWebSerializer(read_only=True)

    class Meta:
        model = Interest
        fields = ("id", "interest", "comment", "user", "created")


class InterestedStatisticWebV2Serializer(serializers.ModelSerializer):
    user = InterestedStatisticUserWebSerializer(read_only=True)
    interest_sort = serializers.SerializerMethodField()

    class Meta:
        model = Interest
        fields = ("id", "interest", "comment", "user", "created", "interest_sort")

    def get_interest_sort(self, obj):
        if obj.interest == Interest.INTEREST_YES:
            if datetime.now().strftime("%A") == "Monday":
                start_date = pytz.utc.localize(
                    datetime.combine((datetime.now().date() - timedelta(2)), time())
                )
            else:
                start_date = pytz.utc.localize(
                    datetime.combine((datetime.now().date() - timedelta(1)), time())
                )
            if obj.created >= start_date:
                return True
            return False
        return False


class UserStatisticSerializerMixin(serializers.ModelSerializer):
    avatar = serializers.ImageField(source="avatar_thumbnail_square", read_only=True)
    agency_name = serializers.CharField(source="agency.name", allow_null=True)
    house_id = serializers.SerializerMethodField()
    house_address = serializers.SerializerMethodField()
    raw_address = serializers.SerializerMethodField()
    street_number = serializers.SerializerMethodField()
    hide_address = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            "uuid",
            "full_name",
            "email",
            "agency_name",
            "avatar",
            "phone",
            "state",
            "house_id",
            "house_address",
            "raw_address",
            "street_number",
            "hide_address",
            "user_type",
        )

    def get_user_type(self, obj):
        return obj.user_type

    def get_house_address(self, obj):
        house_id = self.context.get("request").parser_context.get("kwargs").get("pk")
        house = get_object_or_404(House, pk=house_id)
        return house.raw_address
        # return house.address

    def get_raw_address(self, obj):
        house_id = self.context.get("request").parser_context.get("kwargs").get("pk")
        house = get_object_or_404(House, pk=house_id)
        return house.raw_address

    def get_hide_address(self, obj):
        house_id = self.context.get("request").parser_context.get("kwargs").get("pk")
        house = get_object_or_404(House, pk=house_id)
        return house.hide_address

    def get_street_number(self, obj):
        house_id = self.context.get("request").parser_context.get("kwargs").get("pk")
        house = get_object_or_404(House, pk=house_id)
        return house.street_number

    def get_house_id(self, obj):
        return self.context.get("request").parser_context.get("kwargs").get("pk")


class UserStatisticSerializer(UserStatisticSerializerMixin):
    pass


class MessagesStatisticSerializer(
    UserContextSerializerMixin, serializers.ModelSerializer
):
    creator = UserStatisticSerializer()
    house = ChatHouseSerializer()
    participants = UserStatisticSerializer(many=True)

    class Meta:
        model = Chat
        fields = (
            "id",
            "chat_id",
            "last_message_at",
            "creator",
            "house",
            "participants",
        )


class UpcomingAppointmentsStatisticSerializer(serializers.ModelSerializer):
    scheduled_date = DateTimeRangeField()
    sender = UserStatisticSerializer(read_only=True)
    recipient = UserStatisticSerializer(read_only=True)
    house = SeparatedReadWriteField(read_field=AppointmentHouseSerializer())

    class Meta:
        model = UserAppointment
        fields = (
            "id",
            "sender",
            "house",
            "recipient",
            "scheduled_date",
            "appointment_type",
            "is_active",
        )
        read_only_fields = ("id", "appointment_type")


class InterestedStatisticSerializer(serializers.ModelSerializer):
    user = UserStatisticSerializer()

    class Meta:
        model = Interest
        fields = ("id", "interest", "comment", "user", "created")


class InterestedStatisticV2Serializer(serializers.ModelSerializer):
    user = UserStatisticSerializer()
    interest_sort = serializers.SerializerMethodField()

    class Meta:
        model = Interest
        fields = ("id", "interest", "comment", "user", "created", "interest_sort")

    def get_interest_sort(self, obj):
        if obj.interest == Interest.INTEREST_YES:
            if datetime.now().strftime("%A") == "Monday":
                start_date = pytz.utc.localize(
                    datetime.combine((datetime.now().date() - timedelta(2)), time())
                )
            else:
                start_date = pytz.utc.localize(
                    datetime.combine((datetime.now().date() - timedelta(1)), time())
                )
            if obj.created >= start_date:
                return True
            return False
        return False


class SentToUserStatisticWebSerializer(UserStatisticWebSerializerMixin):
    created = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "full_name", "email", "avatar", "phone", "created")

    def get_created(self, obj):
        house_id = self.context.get("request").parser_context.get("kwargs").get("pk")
        house = get_object_or_404(House, pk=house_id)
        return house.created
