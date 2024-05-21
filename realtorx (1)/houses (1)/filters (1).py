from django.db.models import Exists, OuterRef, Q

from rest_framework.filters import BaseFilterBackend

from django_filters import rest_framework as filters

from realtorx.houses.models import House, Interest, SavedFilter
from realtorx.houses.utils import get_address_from_point, get_point_from_address
from localflavor.us.us_states import STATE_CHOICES


class SavedFiltersFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        filters_to_apply = request.query_params.get("apply_saved_filters")

        if not filters_to_apply or not isinstance(filters_to_apply, str):
            return queryset

        user_filters = SavedFilter.objects.filter(user=request.user)
        if filters_to_apply != "all":
            user_filters = user_filters.filter(pk__in=filters_to_apply.split(","))

        return user_filters.apply(queryset)


class InterestFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        interest_value = request.query_params.get("interest")

        if not interest_value:
            return queryset

        return queryset.annotate(
            matched_interests_exists=Exists(
                Interest.objects.filter(
                    user=request.user, house=OuterRef("id"), interest=interest_value
                ),
            ),
        ).filter(matched_interests_exists=True)


class HouseInterestFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        interest_value = request.query_params.get("interest")

        if not interest_value:
            return queryset

        return (
            queryset.filter(
                user=request.user,
                interest=interest_value,
                house__status=House.HOUSE_STATUSES.published,
            )
            .exclude(house__main_photo__isnull=True)
            .exclude(house__main_photo__exact="")
        )


class HousesFilterSet(filters.FilterSet):
    class Meta:
        model = House
        fields = {
            "user__uuid": ["exact"],
        }


class HouseStatusFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        status = request.query_params.get("status")

        if status:
            queryset = queryset.filter(status=status)
        elif view.action in ["list"]:
            queryset = queryset.filter(status=House.HOUSE_STATUSES.published)

        return queryset


class MyHouseInterestsFilterSet(filters.FilterSet):
    class Meta:
        model = Interest
        fields = {
            "interest": ["exact"],
        }


class HouseSearchFilterSetV1(filters.FilterSet):
    """
    added filters for search screen in mobile app and webapp.
    """

    county = filters.CharFilter(method="_county_filter")
    city = filters.CharFilter(method="_city_filter")
    state = filters.CharFilter(method="_state_filter")
    geocode_address = filters.CharFilter(method="_geocode_address_filter")
    baths_count = filters.CharFilter(method="_baths_count_filter")
    bedrooms_count = filters.CharFilter(method="_bedrooms_count_filter")
    carparks_count = filters.CharFilter(method="_carparks_count_filter")
    land_size = filters.CharFilter(method="_land_size_filter")
    land_size_unit = filters.CharFilter(method="_land_size_unit_filter")
    property_size = filters.CharFilter(method="_property_size_filter")
    property_type = filters.CharFilter(method="_property_type_filter")

    class Meta:
        model = House
        fields = {
            "state": ["exact"],
        }

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

    def _county_filter(self, queryset, name, value):
        return queryset.filter(
            Q(county__iexact=value) | Q(county__iexact="") | Q(county__isnull=True)
        )

    def _state_filter(self, queryset, name, value):
        state = value
        if type(value) == str:
            state = [item for item in STATE_CHOICES if value in item]
        if state:
            return queryset.filter(
                Q(state__in=state[0]) | Q(state__iexact="") | Q(state__isnull=True)
            ).distinct()
        return queryset

    def _city_filter(self, queryset, name, value):
        return queryset.filter(
            Q(city__iexact=value) | Q(city__iexact="") | Q(city__isnull=True)
        )

    def _baths_count_filter(self, queryset, name, value):
        return queryset.filter(Q(baths_count__gte=value) | Q(baths_count__isnull=True))

    def _carparks_count_filter(self, queryset, name, value):
        return queryset.filter(
            Q(carparks_count__gte=value) | Q(carparks_count__isnull=True)
        )

    def _bedrooms_count_filter(self, queryset, name, value):
        return queryset.filter(
            Q(bedrooms_count__gte=value) | Q(bedrooms_count__isnull=True)
        )

    def _land_size_filter(self, queryset, name, value):
        return queryset.filter(Q(land_size__gte=value) | Q(land_size__isnull=True))

    def _land_size_unit_filter(self, queryset, name, value):
        return queryset.filter(
            Q(land_size_units__iexact=value)
            | Q(land_size_units__iexact="")
            | Q(land_size_units__isnull=True)
        )

    def _property_size_filter(self, queryset, name, value):
        return queryset.filter(
            Q(internal_land_size__gte=value) | Q(internal_land_size__isnull=True)
        )

    def _property_type_filter(self, queryset, name, value):
        return queryset.filter(
            Q(house_type__iexact=value)
            | Q(house_type__iexact="")
            | Q(house_type__isnull=True)
        )
