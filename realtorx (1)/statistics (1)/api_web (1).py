from rest_framework.filters import OrderingFilter

from realtorx.statistics.api_mixins import (
    StatisticViewSetMixin,
    StatisticViewSetMixinV2,
)
from realtorx.statistics.serializers import (
    InterestedStatisticWebSerializer,
    InterestedStatisticWebV2Serializer,
    MessagesStatisticWebSerializer,
    UpcomingAppointmentsStatisticWebSerializer,
    UserStatisticWebSerializer,
    SentToUserStatisticWebSerializer,
)


class StatisticWebViewSet(StatisticViewSetMixin):
    filter_backends = (OrderingFilter,)

    @property
    def ordering_fields(self):
        # For objects_by_statistic action only
        statistic_name = self.request.query_params.get("statistic_name")

        if statistic_name is None or self.action != "objects_by_statistic":
            return None

        if statistic_name in ["interested", "not_interested"]:
            return ["user__full_name", "created"]

        if statistic_name == "messages":
            return ["recipient__full_name", "creator__full_name", "last_message_at"]

        if statistic_name == "upcoming_appointments":
            return ["scheduled_date", "sender__full_name"]

        if statistic_name == "sent_to":
            return ["user__full_name", "created"]

    def get_serializer_class(self):
        if self.action == "objects_by_statistic":
            if self.request.query_params.get("statistic_name") == "sent_to":
                return SentToUserStatisticWebSerializer
            return next(
                (
                    serializer_class
                    for serializer_class in [
                        InterestedStatisticWebSerializer,
                        MessagesStatisticWebSerializer,
                        UserStatisticWebSerializer,
                        UpcomingAppointmentsStatisticWebSerializer,
                    ]
                    if self.get_queryset().model == serializer_class.Meta.model
                )
            )
        return super().get_serializer_class()


class StatisticWebViewSetV2(StatisticWebViewSet, StatisticViewSetMixinV2):

    def get_serializer_class(self):
        if self.action == "objects_by_statistic":
            if self.request.query_params.get("statistic_name") == "sent_to":
                return SentToUserStatisticWebSerializer
            return next(
                (
                    serializer_class
                    for serializer_class in [
                        InterestedStatisticWebV2Serializer,
                        MessagesStatisticWebSerializer,
                        UserStatisticWebSerializer,
                        UpcomingAppointmentsStatisticWebSerializer,
                    ]
                    if self.get_queryset().model == serializer_class.Meta.model
                )
            )
        return super().get_serializer_class()
