from django_filters import rest_framework as filters

from realtorx.custom_auth.models import ApplicationUser


class UsersFilterSet(filters.FilterSet):
    class Meta:
        model = ApplicationUser
        fields = {}
