import operator
from functools import reduce

from django.contrib.auth import get_user_model
from django.db.models import Q

from django_filters import rest_framework as filters
from django_filters.rest_framework import FilterSet

from realtorx.custom_auth.models import ApplicationUser

User = get_user_model()


class RegistrationFilterSet(FilterSet):
    phone__in = filters.CharFilter(method="_following_status_filter")

    def _following_status_filter(self, queryset, name, value):
        # NOTE: If you add any changes in the logic here, also modify the logic at
        # following.serializers.AutoConnectionsSerializer and
        # following.tasks.process_following_requests_from_phone

        for _ in (" ", "-", "+", "#", "*", "(", ")"):
            value = value.replace(_, "")

        phones = [phone[-9:] for phone in value.split(",") if len(phone) >= 9]
        # phones = [phone[-10:] for phone in value.split(',') if len(phone) >= 9]
        # filter_query = Q()
        # for phone in phones:
        #     filter_query = filter_query | Q(phone__endswith=phone)

        # return queryset.filter(filter_query)
        if len(phones) == 0:
            return queryset.none()
        filter_querys = (
            queryset.filter(
                reduce(operator.or_, (Q(phone__endswith=x) for x in phones))
            )
            .exclude(id=self.request.user.id)
            .distinct()
        )  # removed self user from queryset filter

        if "my_connection" in self.request.query_params:
            if self.request.query_params.get("my_connection") == "yes":
                return filter_querys.exclude(
                    Q(full_name="")
                    | Q(user_type=ApplicationUser.TYPE_CHOICES.buyer)
                    | Q(user_type=ApplicationUser.TYPE_CHOICES.trial)
                )
            else:
                return filter_querys.exclude(full_name="")
        return filter_querys.exclude(full_name="")
