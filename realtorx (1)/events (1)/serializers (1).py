from django.contrib.auth import get_user_model

from rest_framework import serializers

from realtorx.events.models import Event
from realtorx.houses.models import House
from realtorx.utils.serializers.fields import LookupRelatedField

User = get_user_model()


class ResetEventsSerializer(serializers.Serializer):
    # chat_id = LookupRelatedField(queryset=Chat.objects.all(), lookup_field='chat_id', required=False)
    connection_sender = LookupRelatedField(
        queryset=User.objects.all(), lookup_field="uuid", required=False
    )
    house_id = LookupRelatedField(
        queryset=House.objects.all(), lookup_field="id", required=False
    )
    type = serializers.ChoiceField(choices=Event.EVENT_TYPES)
