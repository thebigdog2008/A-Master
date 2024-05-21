from django.db.models import Q

from rest_framework.filters import BaseFilterBackend

from django_filters import rest_framework as filters
from model_utils import Choices
from realtorx.custom_auth.models import ApplicationUser
from realtorx.following.models import FollowingRequest
from realtorx.houses.utils import get_point_from_address, get_address_from_point
from localflavor.us.us_states import STATE_CHOICES


class FollowingFilterSet(filters.FilterSet):
    TYPES = Choices(("in", "in"), ("out", "out"), ("none", "none"))

    following_status = filters.CharFilter(method="_following_status_filter")
    following_type = filters.ChoiceFilter(
        choices=TYPES,
        method="_following_type_filter",
    )
    my_connection_list = filters.BooleanFilter(method="_my_connection_list")
    county = filters.CharFilter(method="_county_filter")
    city = filters.CharFilter(method="_city_filter")

    class Meta:
        model = ApplicationUser
        fields = {
            "state": ["exact"],
        }

    def _county_filter(self, queryset, name, value):
        if value.lower() != "all":
            return queryset.filter(county__icontains=value.replace(" County", ""))
            # items = value.split()
            # commented code to fix search filter
            # if 'County' in items:
            #     items.remove('County')

            # if len(items) < 2:
            #     return queryset.filter(county__overlap=[' '.join(items), value])
            # combinations = []
            # for i in range(len(items) + 1):
            #     for combination in itertools.combinations(items, i):
            #         combinations.append(combination)
            # return queryset.filter(
            #     county__overlap=[' '.join(combination) for combination in combinations if len(combination) > 1],
            # )

        return queryset

    def _city_filter(self, queryset, name, value):
        if value.lower() != "all":
            if ", " in value:
                val = value.split(", ")
            else:
                val = value.split(",")
            return queryset.filter(city__overlap=val)
        return queryset

    def _following_type_filter(self, queryset, name, value):
        if value == "in":
            ids = FollowingRequest.objects.filter(
                recipient=self.request.user
            ).values_list("sender_id", flat=True)
        elif value == "out":
            ids = FollowingRequest.objects.filter(sender=self.request.user).values_list(
                "recipient_id", flat=True
            )
        elif value == "none":
            ids = []
            all_ids = FollowingRequest.objects.filter(
                Q(sender=self.request.user) | Q(recipient=self.request.user),
            ).values_list("sender_id", "recipient_id")
            for i in all_ids:
                ids = ids + list(i)
            return queryset.exclude(id__in=ids)

        else:
            return queryset
        return queryset.filter(id__in=ids)

    def _following_status_filter(self, queryset, name, value):
        q = FollowingRequest.objects.filter(
            Q(sender=self.request.user) | Q(recipient=self.request.user),
        )
        if value == "any":
            filter_kwarg = {"status__isnull": False}
        else:
            filter_kwarg = {"status": value}

        ids = []
        all_ids = q.filter(**filter_kwarg).values_list("sender_id", "recipient_id")
        for i in all_ids:
            ids = ids + list(i)
        return queryset.filter(id__in=ids)

    def _my_connection_list(self, queryset, name, value):
        """
        Filter for fetching all users that accepted or have pending status of incomig or outcoming requests
        """
        if not value:
            return
        return queryset.filter(
            Q(
                id__in=self.request.user.out_coming_requests.all().values_list(
                    "recipient_id", flat=True
                ),
            )
            | Q(
                id__in=self.request.user.in_coming_requests.all().values_list(
                    "sender_id", flat=True
                ),
            ),
        )


class FollowingFilterSetV2(filters.FilterSet):
    TYPES = Choices(("in", "in"), ("out", "out"), ("none", "none"))

    following_status = filters.CharFilter(method="_following_status_filter")
    following_type = filters.ChoiceFilter(
        choices=TYPES,
        method="_following_type_filter",
    )
    my_connection_list = filters.BooleanFilter(method="_my_connection_list")
    category = filters.CharFilter(method="_category_filter")
    county = filters.CharFilter(method="_county_filter")
    state = filters.CharFilter(method="_state_filter")
    city = filters.CharFilter(method="_city_filter")
    geocode_address = filters.CharFilter(method="_geocode_address_filter")
    baths_count = filters.CharFilter(method="_baths_count_filter")
    carparks_count = filters.CharFilter(method="_carparks_count_filter")
    bedrooms_count = filters.CharFilter(method="_bedrooms_count_filter")
    price = filters.CharFilter(method="_price_filter")
    land_size_min = filters.CharFilter(method="_land_size_min_filter")
    property_size_min = filters.CharFilter(method="_property_size_min_filter")
    property_type = filters.CharFilter(method="_property_type_filter")

    class Meta:
        model = ApplicationUser
        fields = {
            "state": ["exact"],
        }

    def _following_status_filter(self, queryset, name, value):
        q = FollowingRequest.objects.filter(
            Q(sender=self.request.user) | Q(recipient=self.request.user),
        )
        if value == "any":
            filter_kwarg = {"status__isnull": False}
        else:
            filter_kwarg = {"status": value}

        ids = []
        all_ids = q.filter(**filter_kwarg).values_list("sender_id", "recipient_id")
        for i in all_ids:
            ids = ids + list(i)
        return queryset.filter(id__in=ids).distinct()

    def _county_filter(self, queryset, name, value):
        return queryset.filter(
            Q(saved_filters__county__iexact=value)
            | Q(saved_filters__county__iexact="")
            | Q(saved_filters__county__isnull=True)
        )

    def _state_filter(self, queryset, name, value):
        state = value
        if type(value) == str:
            state = [item for item in STATE_CHOICES if value in item]
        if state:
            return queryset.filter(
                Q(saved_filters__state__in=state[0])
                | Q(saved_filters__state__iexact="")
                | Q(saved_filters__state__isnull=True)
            )
        return queryset

    def _city_filter(self, queryset, name, value):
        if value.lower() != "all":
            if ", " in value:
                val = value.split(", ")
            else:
                val = value.split(",")
            return queryset.filter(
                Q(saved_filters__city__overlap=val)
                | Q(saved_filters__city__iexact="{}")
                | Q(saved_filters__city__isnull=True)
            )

        return queryset

    def _geocode_address_filter(self, queryset, name, value):
        point = get_point_from_address(value)
        address = get_address_from_point(point)

        if address is not None:
            county = address[7]
            state = address[4]
            city = address[3]
            state = [item for item in STATE_CHOICES if state in item]
            queryset = self._county_filter(queryset, name, county)
            queryset = self._state_filter(queryset, name, state)
            queryset = self._city_filter(queryset, name, city)
        return queryset

    def _category_filter(self, queryset, name, value):
        return queryset.filter(Q(saved_filters__action__contains=value)).distinct()

    def _baths_count_filter(self, queryset, name, value):
        return queryset.filter(
            Q(saved_filters__baths_count_min__lte=value)
            | Q(saved_filters__baths_count_min__isnull=True)
        )

    def _carparks_count_filter(self, queryset, name, value):
        return queryset.filter(
            Q(saved_filters__carparks_count_min__lte=value)
            | Q(saved_filters__carparks_count_min__isnull=True)
        )

    def _bedrooms_count_filter(self, queryset, name, value):
        return queryset.filter(
            Q(saved_filters__bedrooms_count_min__lte=value)
            | Q(saved_filters__bedrooms_count_min__isnull=True)
        )

    def _price_filter(self, queryset, name, value):
        return queryset.filter(
            Q(saved_filters__price_min__lte=value)
            | Q(saved_filters__price_min__isnull=True),
            Q(saved_filters__price_max__gte=value)
            | Q(saved_filters__price_max__isnull=True),
        )

    def _land_size_min_filter(self, queryset, name, value):
        return queryset.filter(
            Q(saved_filters__land_size_min__lte=value)
            | Q(saved_filters__land_size_min__isnull=True)
        )

    def _property_size_min_filter(self, queryset, name, value):
        return queryset.filter(
            Q(saved_filters__internal_land_size_min__lte=value)
            | Q(saved_filters__internal_land_size_min__isnull=True)
        ).distinct()

    def _property_type_filter(self, queryset, name, value):
        return queryset.filter(
            Q(saved_filters__house_types__contains=value.split(" "))
            | Q(saved_filters__house_types__isnull=True)
        ).distinct()

    def _following_type_filter(self, queryset, name, value):
        if value == "in":
            ids = FollowingRequest.objects.filter(
                recipient=self.request.user
            ).values_list("sender_id", flat=True)
        elif value == "out":
            ids = FollowingRequest.objects.filter(sender=self.request.user).values_list(
                "recipient_id", flat=True
            )
        elif value == "none":
            ids = []
            all_ids = FollowingRequest.objects.filter(
                Q(sender=self.request.user) | Q(recipient=self.request.user),
            ).values_list("sender_id", "recipient_id")
            for i in all_ids:
                ids = ids + list(i)
            return queryset.exclude(id__in=ids).distinct()

        else:
            return queryset
        return queryset.filter(id__in=ids)

    def _my_connection_list(self, queryset, name, value):
        """
        Filter for fetching all users that accepted or have pending status of incomig or outcoming requests
        """
        if not value:
            return
        return queryset.filter(
            Q(
                id__in=self.request.user.out_coming_requests.all().values_list(
                    "recipient_id", flat=True
                ),
            )
            | Q(
                id__in=self.request.user.in_coming_requests.all().values_list(
                    "sender_id", flat=True
                ),
            ),
        ).distinct()


class AgencyFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        agency_id = request.query_params.get("agency")
        if agency_id is None:
            return queryset

        try:
            agency_id = int(agency_id)
        except ValueError:
            return queryset

        if agency_id == 0:
            return queryset

        return queryset.filter(agency=agency_id)
