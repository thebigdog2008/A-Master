from rest_framework import mixins
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from django_filters.rest_framework import DjangoFilterBackend
from unicef_restlib.views import MultiSerializerViewSetMixin, NestedViewSetMixin

from realtorx.houses.filters import HouseStatusFilterBackend, MyHouseInterestsFilterSet
from realtorx.houses.models import House, Interest
from realtorx.houses.permissions import IsHouseCreator
from realtorx.houses.serializers.house import owned as my_serializers
from realtorx.houses.serializers.interest import InterestListSerializer
from realtorx.permissions.views import SimplePermittedFSMTransitionActionMixin
from realtorx.utils.filters import StupidSearchFilter


class MyHousesViewSet(
    SimplePermittedFSMTransitionActionMixin,
    MultiSerializerViewSetMixin,
    NestedViewSetMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = House.objects.all().order_by("-created")
    serializer_class = my_serializers.HouseDetailSerializer
    filter_backends = (
        StupidSearchFilter,
        HouseStatusFilterBackend,
        OrderingFilter,
    )
    search_fields = ("raw_address",)
    ordering_fields = [
        "address",
        "messages",
        "upcoming_appointments",
        "last_activity",
        "interested",
        "not_interested",
        "sent_to_count",
        "day_interested",
        "created",
    ]
    serializer_action_classes = {
        "list": my_serializers.HouseWebWithStatisticListSerializer,
        "retrieve": my_serializers.HouseDetailPageWithStatisticWebSerializer,
    }
    permission_classes = [IsAuthenticated, IsHouseCreator]
    transition_permission_classes = {
        "publish": [IsHouseCreator],
        "archive": [IsHouseCreator],
    }

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                user=self.request.user,
            )
            .with_upcoming_appointments_amount()
            .with_chats_amount()
            .with_not_interested_users_amount()
            .with_interested_users_amount()
            .with_day_interested_users_amount()
        )


class MyHouseInterestsViewSet(
    NestedViewSetMixin, mixins.ListModelMixin, GenericViewSet
):
    queryset = Interest.objects.all().select_related("user").order_by("-created")
    serializer_class = InterestListSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = MyHouseInterestsFilterSet
    ordering_fields = ["user__full_name", "created"]
