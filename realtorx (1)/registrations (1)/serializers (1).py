from rest_framework import serializers
from realtorx.properties.models import KeyValue
from realtorx.custom_auth.models import ApplicationUser

from realtorx.registrations.serializers_base import (
    RegistrationSerializerBase,
    RegistrationSerializerBaseV2,
)


class RegistrationSerializer(RegistrationSerializerBase):
    class Meta(RegistrationSerializerBase.Meta):
        ref_name = "RegistrationSerializer"


class RegistrationSerializerV2(RegistrationSerializerBaseV2):
    pass


class RegistrationSerializerV3(RegistrationSerializerBase):
    class Meta(RegistrationSerializerBase.Meta):
        ref_name = "RegistrationSerializerV3"


class RegistrationSerializerV4(RegistrationSerializerBase):
    connection_type = serializers.SerializerMethodField(read_only=True)

    class Meta(RegistrationSerializerBase.Meta):
        ref_name = "RegistrationSerializerV4"
        fields = RegistrationSerializerBase.Meta.fields + ("connection_type",)

    def get_connection_type(self, obj):
        followers = obj.following.filter(id__in=[self.context.get("request").user.id])
        in_follow = obj.in_coming_requests.filter(
            sender__id__in=[self.context.get("request").user.id]
        )
        out_follow = obj.out_coming_requests.filter(
            recipient__id__in=[self.context.get("request").user.id]
        )

        if not followers and not in_follow and not out_follow:
            return "new_connection"
        elif followers:
            return "connected_connection"
        elif in_follow:
            return "in_coming_connection"
        elif out_follow:
            return "out_going_connection"
        else:
            return "new_connection"


def check_phone_number_is_exist_or_not(trial_user_phone):
    if ApplicationUser.objects.filter(phone="+1" + trial_user_phone.value).exists():
        update_obj = KeyValue.objects.get(key="trial_user_phone")
        update_obj.value = str(int(trial_user_phone.value) + 1)
        update_obj.save()
        return check_phone_number_is_exist_or_not(update_obj)
    else:
        return KeyValue.objects.get(key="trial_user_phone").value


class TrialUserSerializer(serializers.ModelSerializer):
    # token = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ApplicationUser
        fields = ("full_name", "username", "phone", "user_type", "uuid")
        extra_kwargs = {
            "username": {"required": False},
            "phone": {"required": False},
            "password": {"required": False},
            "full_name": {"read_only": True},
        }

    def create(self, validated_data):
        trial_user_phone = KeyValue.objects.get(key="trial_user_phone")
        testing_phone = check_phone_number_is_exist_or_not(trial_user_phone)
        validated_data.update(
            {
                "first_name": "testing user",
                "last_name": str(testing_phone),
                "username": str(testing_phone),
                "phone": "+1" + str(testing_phone),
                "user_type": "trial",
                "password": "Temp@123",
            }
        )

        return ApplicationUser.objects.create(**validated_data)
