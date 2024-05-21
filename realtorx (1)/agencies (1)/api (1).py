from rest_framework import mixins, viewsets
from rest_framework.filters import OrderingFilter

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from realtorx.agencies.models import Agency, AgencyBranch
from realtorx.agencies.serializers import AgencySerializer, AgencyAddressSerializer
from realtorx.utils.filters import StupidSearchFilter
from rest_framework.decorators import action
from rest_framework.response import Response


class AgenciesViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Agency.objects.all()
    serializer_class = AgencySerializer
    filter_backends = (
        DjangoFilterBackend,
        OrderingFilter,
        StupidSearchFilter,
    )
    ordering_fields = ["id", "name"]
    ordering = ["name"]
    search_fields = ["name"]

    def list(self, request, *args, **kwargs):
        response = super(AgenciesViewSet, self).list(request, *args, **kwargs)
        with_all = request.query_params.get("with_all")
        page = request.query_params.get("page")
        if (
            with_all is not None
            and with_all.lower() in ("1", "true", "yes")
            and (page == "1" or page is None)
        ):
            if "results" in response.data:
                response.data["results"] = [
                    {"id": 0, "name": "All", "about": ""}
                ] + response.data["results"]
            else:
                response.data = [{"id": 0, "name": "All", "about": ""}] + response.data

        return response

    @action(
        methods=["GET"],
        url_name="agency_address",
        url_path="agency-address",
        detail=False,
        serializer_class=AgencyAddressSerializer,
        permission_classes=[IsAuthenticated],
    )
    def agency_address(self, request, *args, **Kwargs):
        """
        This api is used for getting agency address according there city, state, county and company
        """
        agency = request.query_params.get("agency", None)
        city = request.query_params.get("city", None)
        state = request.query_params.get("state", None)
        county = request.query_params.get("county", None)
        if agency and city and state and county is not None:
            # if county.lower().endswith('county'):
            #     county = county.lower().replace(' county', '')
            queryset = AgencyBranch.objects.filter(
                city=city, state=state, county=county, agency_id=agency
            )
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response()

    @action(methods=["GET"], url_name="agency", url_path="agency", detail=False)
    def agency(self, request, *args, **kwargs):
        """
        This api is used for getting agency according there city, state, county
        """
        response = AgenciesViewSet.list(self, request, *args, **kwargs)
        city = request.query_params.get("city", "")
        state = request.query_params.get("state", "")
        county = request.query_params.get("county", "")
        name = request.query_params.get("search", "")
        if city == "" and state == "" and county == "" and name == "":
            return Response(response.data)
        else:
            # if county != '':
            #     if county.lower().endswith('county'):
            #         county = county.lower().replace(' county', '')
            if county != "" and state != "" and city != "":
                query_filter = {
                    "city__iexact": city,
                    "state__iexact": state,
                    "county__iexact": county,
                }
            elif state != "" and city != "":
                query_filter = {"city__iexact": city, "state__iexact": state}
            elif city != "":
                query_filter = {"city__iexact": city}
            elif state != "":
                query_filter = {"state__iexact": state}
            elif county != "":
                query_filter = {"county__iexact": county}
            else:
                query_filter = {}

            queryset = (
                AgencyBranch.objects.filter(**query_filter)
                .values_list("agency_id", flat=True)
                .distinct()
            )
            if name != "":
                queryset = Agency.objects.filter(id__in=queryset, name__icontains=name)
            else:
                queryset = Agency.objects.filter(id__in=queryset)
            page = self.paginate_queryset(queryset.order_by("name"))
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset.order_by("name"), many=True)
            return Response(serializer.data)
