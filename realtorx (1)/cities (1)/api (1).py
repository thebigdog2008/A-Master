from django.utils.translation import gettext as _

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from django_filters.rest_framework import DjangoFilterBackend

from realtorx.cities.filters import CitiesFilter
from realtorx.cities.models import City
from realtorx.cities.serializers import CitySerializer, CountySerializer


class CitiesViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = City.objects.all()
    filterset_class = CitiesFilter
    serializer_class = CitySerializer
    filter_backends = (
        DjangoFilterBackend,
        OrderingFilter,
    )
    pagination_class = None
    ordering_fields = ["name"]

    def get_serializer_class(self):
        if self.action == "get_counties_by_state":
            return CountySerializer
        return super(CitiesViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        response = super(CitiesViewSet, self).list(request, *args, **kwargs)
        with_all = request.query_params.get("with_all")

        if with_all is not None and with_all.lower() in ("1", "true", "yes"):
            response.data = [
                {"value": "all", "display_name": "All", "zip_codes": []}
            ] + response.data

        return response

    @action(detail=False, methods=["GET"])
    def get_counties_by_state(self, request, *args, **kwargs):
        if not request.query_params.get("state"):
            return Response(
                _("State should be sent"),
                status=HTTP_400_BAD_REQUEST,
            )
        state = request.query_params.get("state")
        queryset = list(self._filter_queryset_with_state(self.get_queryset(), state))
        serializer = self.get_serializer(queryset, many=True)

        with_all = request.query_params.get("with_all")

        if with_all is not None and with_all.lower() in ("1", "true", "yes"):
            data = [{"value": "all", "display_name": "All"}] + serializer.data
            return Response(data)
        return Response(serializer.data)

    def _filter_queryset_with_state(self, queryset, state):
        return (
            queryset.filter(state=state)
            .order_by("county")
            .distinct("county")
            .values("county")
        )

    @action(detail=False, methods=["GET"])
    def get_zip_codes(self, request, *args, **kwargs):
        if not request.query_params.get("name__in"):
            return Response(
                _("Cities should be sent"),
                status=HTTP_400_BAD_REQUEST,
            )
        queryset = self.filter_queryset(self.get_queryset())
        data = []
        for city in queryset:
            data = data + city.zip_codes

        data.sort()
        with_all = request.query_params.get("with_all")
        if with_all is not None and with_all.lower() in ("1", "true", "yes"):
            return Response(["All"] + data)

        return Response(data)
