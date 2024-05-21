from django.db.models import QuerySet

from rest_framework import viewsets, generics
from rest_framework.permissions import AllowAny

from realtorx.custom_auth.models import ApplicationUser
from realtorx.houses.filters import HouseSearchFilterSetV1
from realtorx.houses.models import SavedFilter, House
from realtorx.houses.serializers.house.owned import (
    HouseListSerializer,
    JustBrowsingHouseListSerializer,
)
from realtorx.houses.serializers.saved_filters import SavedFilterSerializer
from realtorx.houses.serializers.saved_filters_v2 import (
    SavedFilterSerializer as SavedFilterV2Serializer,
)


class SavedFiltersViewSet(viewsets.ModelViewSet):
    serializer_class = SavedFilterSerializer
    queryset = SavedFilter.objects

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(user=self.request.user)


class SavedFiltersV2ViewSet(viewsets.ModelViewSet):
    serializer_class = SavedFilterV2Serializer
    queryset = SavedFilter.objects

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(user=self.request.user)


class MySearchHousesViewSet(generics.ListAPIView, viewsets.GenericViewSet):
    """
    added my search house view set to create api for search screen in mobile app and webapp.
    """

    queryset = House.objects.all()
    serializer_class = HouseListSerializer
    filterset_class = HouseSearchFilterSetV1

    def get_queryset(self) -> QuerySet:
        """
        override queryset to get all the my sent house list.
        """
        currentuser = ApplicationUser.objects.get(id=self.request.user.id)
        houses = currentuser.sent_to_users.all()
        houses = houses.filter(status=House.HOUSE_STATUSES.published)
        return houses


class JustBrowsingHousesViewSet(generics.ListAPIView, viewsets.GenericViewSet):
    """
    added just browsing for guest user login.
    """

    queryset = House.objects.filter(is_demo_property=True)
    serializer_class = JustBrowsingHouseListSerializer
    permission_classes = [AllowAny]
