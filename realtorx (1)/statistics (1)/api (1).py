from realtorx.statistics.api_mixins import (
    StatisticViewSetMixin,
    StatisticViewSetMixinV2,
)
from realtorx.statistics.serializers import (
    InterestedStatisticSerializer,
    InterestedStatisticV2Serializer,
    MessagesStatisticSerializer,
    UpcomingAppointmentsStatisticSerializer,
    UserStatisticSerializer,
)


class StatisticViewSet(StatisticViewSetMixin):

    @property
    def search_fields(self):
        statistic_name = self.request.query_params.get("statistic_name")

        if statistic_name in ["interested", "not_interested"]:
            return ["user__full_name", "user__agency__name"]

        if statistic_name in ["sent_to", "no_response"]:
            return ["full_name", "agency__name"]

        if statistic_name == "messages":
            return ["participants__full_name", "participants__agency__name"]

        if statistic_name == "upcoming_appointments":
            return ["sender__full_name", "sender__agency__name"]

    def get_serializer_class(self):
        if self.action == "objects_by_statistic":
            return next(
                (
                    serializer_class
                    for serializer_class in [
                        InterestedStatisticSerializer,
                        MessagesStatisticSerializer,
                        UpcomingAppointmentsStatisticSerializer,
                        UserStatisticSerializer,
                    ]
                    if self.get_queryset().model == serializer_class.Meta.model
                )
            )
        return super().get_serializer_class()


class StatisticViewSetV2(StatisticViewSet, StatisticViewSetMixinV2):

    def get_serializer_class(self):
        if self.action == "objects_by_statistic":
            return next(
                (
                    serializer_class
                    for serializer_class in [
                        InterestedStatisticV2Serializer,
                        MessagesStatisticSerializer,
                        UpcomingAppointmentsStatisticSerializer,
                        UserStatisticSerializer,
                    ]
                    if self.get_queryset().model == serializer_class.Meta.model
                )
            )
        return super().get_serializer_class()
