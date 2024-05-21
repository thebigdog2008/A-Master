from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from realtorx.events.cache_utils import get_events_cache_key
from realtorx.events.models import Event
from realtorx.events.serializers import ResetEventsSerializer


class EventViewSet(GenericViewSet):
    def get_events_num_data(self):
        print("called get_events_num_data --->", self.request.user.id)
        return {
            "events_amount": Event.get_cached_unseen_events_count(self.request.user.id),
            "by_type": Event.get_cached_unseen_events_count(
                self.request.user.id, by_type=True
            ),
        }

    @action(
        methods=("get",),
        detail=False,
        permission_classes=(AllowAny,),
        url_path="count",
        url_name="count",
    )
    def events(self, request, *args, **kwargs):
        return Response(data=self.get_events_num_data())

    @action(
        methods=("post",),
        detail=False,
        permission_classes=(AllowAny,),
        url_path="reset",
        url_name="reset",
    )
    def events_reset(self, request, *args, **kwargs):
        print("called events_reset --->")
        user = request.user
        print("user ------>", request.user)
        serializer = ResetEventsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        extra_filters = {}

        #  Filter events by chat
        if "chat_id" in serializer.validated_data:
            extra_filters["chat"] = serializer.validated_data["chat_id"]

        #  Filter events by connection request
        if "connection_sender" in serializer.validated_data:
            extra_filters["initiator"] = serializer.validated_data["connection_sender"]

        #  Filter events by new listing
        if "house_id" in serializer.validated_data:
            extra_filters["house"] = serializer.validated_data["house_id"]

        kind = serializer.validated_data["type"]
        events = Event.get_unseen_user_events(user.id, kind=kind, **extra_filters)
        print(
            "------------> Event.decrement_events_count",
            kind,
            extra_filters,
            events,
            user.id,
        )

        Event.decrement_events_count(
            user.id,
            kind,
            get_events_cache_key(user.id, kind),
            events.count() if events else 0,
            **extra_filters,
        )

        events.update(is_viewed=True)

        return Response(data=self.get_events_num_data())
