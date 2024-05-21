import operator
from functools import reduce

from django.db import models

from rest_framework.compat import distinct
from rest_framework.filters import SearchFilter

from localflavor.us.us_states import STATE_CHOICES


class SearchFilterWithStates(SearchFilter):

    def filter_queryset(self, request, queryset, view):
        search_fields = self.get_search_fields(view, request)
        search_terms = self.get_search_terms(request)

        if not search_fields or not search_terms:
            return queryset

        orm_lookups = [
            self.construct_search(str(search_field)) for search_field in search_fields
        ]

        base = queryset
        conditions = []
        for search_term in search_terms:
            queries = [
                models.Q(**{orm_lookup: search_term}) for orm_lookup in orm_lookups
            ]

            states = []
            for state in STATE_CHOICES:
                if search_term.lower() in state[1].lower():
                    states.append(state[0])
            if states:
                statistic_name = request.query_params.get("statistic_name")

                if statistic_name in ["interested", "not_interested"]:
                    lookup = "user__state__in"

                if statistic_name in ["sent_to", "no_response"]:
                    lookup = "state__in"

                if statistic_name == "messages":
                    lookup = "participants__state__in"

                if statistic_name == "upcoming_appointments":
                    lookup = "sender__state__in"

                queries.append(models.Q(**{lookup: states}))
            conditions.append(reduce(operator.or_, queries))

        queryset = queryset.filter(reduce(operator.and_, conditions))

        if self.must_call_distinct(queryset, search_fields):
            # Filtering against a many-to-many field requires us to
            # call queryset.distinct() in order to avoid duplicate items
            # in the resulting queryset.
            # We try to avoid this if possible, for performance reasons.
            queryset = distinct(queryset, base)
        return queryset
