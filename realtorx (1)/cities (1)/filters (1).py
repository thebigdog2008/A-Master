from django_filters import rest_framework as filters

from realtorx.cities.models import City


class CitiesFilter(filters.FilterSet):
    county__in = filters.CharFilter(method="_county_filter")
    name__in = filters.CharFilter(method="_city_filter")

    class Meta:
        model = City
        fields = {
            "state": ["in"],
            "name": ["exact"],
        }

    def _county_filter(self, queryset, name, value):
        if value.lower() != "all":
            return queryset.filter(county=value)
        return queryset.none()

    def _city_filter(self, queryset, name, value):
        if value.lower() != "all":
            if ", " in value:
                val = value.split(", ")
            else:
                val = value.split(",")
            return queryset.filter(name__in=val)
        return queryset.none()
