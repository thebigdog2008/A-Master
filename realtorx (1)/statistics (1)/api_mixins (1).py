from django.utils.translation import gettext as _

from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.viewsets import GenericViewSet

from realtorx.houses.models.house import House
from realtorx.statistics.permissions import IsOwner
from realtorx.statistics.serializers import StatisticSerializer
from realtorx.statistics.utils import SearchFilterWithStates
from datetime import datetime, timedelta
from django.db.models import Case, Value, When, BooleanField


class StatisticViewSetMixin(RetrieveModelMixin, GenericViewSet):
    STATISTIC_NAMES = [
        "sent_to",
        "interested",
        "not_interested",
        "no_response",
        "messages",
        "upcoming_appointments",
    ]

    queryset = House.objects.defer().all()
    permission_classes = (IsOwner, IsAuthenticated)
    serializer_class = StatisticSerializer

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (  # noqa
            f"Expected view {self.__class__.__name__} to be called with a URL keyword argument "
            f'named "{lookup_url_kwarg}". Fix your URL conf, or set the `.lookup_field` '
            f"attribute on the view correctly."
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action == "objects_by_statistic":
            return queryset.model.objects.get_queryset_by_statistic_name(
                self.request.query_params.get("statistic_name"),
                self.get_object(queryset),
            )
        return queryset.with_statistic()

    def _filter_queryset_with_search(self, queryset):
        queryset = SearchFilterWithStates().filter_queryset(
            self.request, queryset, self
        )

        return self.filter_queryset(queryset)

    @action(
        methods=["get"],
        detail=True,
        url_name="objects_by_statistic",
        url_path="objects-by-statistic",
    )
    def objects_by_statistic(self, request, *args, pk=None, **kwargs):
        if request.query_params.get("statistic_name") not in self.STATISTIC_NAMES:
            return Response(
                _(f"Incorrect statistic name. Correct values:{self.STATISTIC_NAMES}"),
                status=HTTP_400_BAD_REQUEST,
            )

        # Pagination
        page = self.paginate_queryset(
            self._filter_queryset_with_search(self.get_queryset())
        )

        if page is None:
            queryset = list(self._filter_queryset_with_search(self.get_queryset()))
            serializer = self.get_serializer(queryset, many=True)

            return Response(serializer.data)

        serializer = self.get_serializer(page, many=True)

        return self.get_paginated_response(serializer.data)


class StatisticViewSetMixinV2(
    StatisticViewSetMixin, RetrieveModelMixin, GenericViewSet
):

    @action(
        methods=["get"],
        detail=True,
        url_name="objects_by_statistic",
        url_path="objects-by-statistic",
    )
    def objects_by_statistic(self, request, *args, pk=None, **kwargs):
        if request.query_params.get("statistic_name") not in self.STATISTIC_NAMES:
            return Response(
                _(f"Incorrect statistic name. Correct values:{self.STATISTIC_NAMES}"),
                status=HTTP_400_BAD_REQUEST,
            )

        # Pagination
        if request.query_params.get("statistic_name") == "interested":
            page = self.paginate_queryset(
                self._filter_queryset_with_search(self.get_queryset())
                .annotate(
                    interest_sort=Case(
                        When(
                            created__date__gte=datetime.now() - timedelta(1),
                            then=Value(True),
                        ),
                        default=Value(False),
                        output_field=BooleanField(),
                    )
                )
                .order_by("-interest_sort", "-created")
            )
        else:
            page = self.paginate_queryset(
                self._filter_queryset_with_search(self.get_queryset())
            )

        if page is None:
            queryset = list(self._filter_queryset_with_search(self.get_queryset()))
            serializer = self.get_serializer(queryset, many=True)

            return Response(serializer.data)

        serializer = self.get_serializer(page, many=True)

        return self.get_paginated_response(serializer.data)
