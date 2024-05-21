import operator
from functools import reduce

from django.db import models

from rest_framework.compat import distinct
from rest_framework.filters import SearchFilter


class StupidSearchFilter(SearchFilter):
    """we don't split search terms as it would work incorrect"""

    def filter_queryset(self, request, queryset, view):
        search_fields = self.get_search_fields(view, request)
        search_value = request.query_params.get(self.search_param, "")
        search_value = search_value.replace("\x00", "")

        if not search_fields or not search_value:
            return queryset

        orm_lookups = [
            self.construct_search(str(search_field)) for search_field in search_fields
        ]

        base = queryset
        queryset = queryset.filter(
            reduce(
                operator.or_,
                (models.Q(**{lookup: search_value}) for lookup in orm_lookups),
            ),
        )

        if self.must_call_distinct(queryset, search_fields):
            queryset = distinct(queryset, base)
        return queryset
