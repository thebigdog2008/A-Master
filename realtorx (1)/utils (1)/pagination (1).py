from urllib import parse

from rest_framework.pagination import CursorPagination

from unicef_restlib.pagination import DynamicPageNumberPagination


class CursorPaginationWithCursorValueInData(CursorPagination):
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        response = super(
            CursorPaginationWithCursorValueInData, self
        ).get_paginated_response(data)

        next_cursor_url = response.data["next"]
        next_cursor_value = None

        if next_cursor_url:
            parsed = parse.urlparse(next_cursor_url)
            next_cursor_values_list = parse.parse_qs(parsed.query)["cursor"]

            if next_cursor_values_list:
                next_cursor_value = next_cursor_values_list[0]

        response.data["next_cursor_value"] = next_cursor_value

        return response

    def encode_cursor(self, cursor):
        return parse.unquote(
            super(CursorPaginationWithCursorValueInData, self).encode_cursor(cursor)
        )


class SwitchableCursorPaginationViewMixin:
    @property
    def paginator(self):
        queryset = self.filter_queryset(self.get_queryset())
        paginator = super().paginator

        if isinstance(paginator, CursorPagination):
            order_by = queryset.query.order_by

            if order_by:
                paginator.ordering = order_by
            elif queryset.query.default_ordering:
                paginator.ordering = queryset.model._meta.ordering

        return paginator

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        if "count" not in response.data:
            response.data["count"] = self.filter_queryset(self.get_queryset()).count()
        return response

    @property
    def pagination_class(self):
        cursor_pagination = self.request.query_params.get("cursor_pagination")

        if cursor_pagination and cursor_pagination.upper() == "TRUE":
            return CursorPaginationWithCursorValueInData
        return DynamicPageNumberPagination
