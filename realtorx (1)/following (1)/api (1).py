from datetime import datetime, timedelta

from django.db.models import Case, CharField, F, OuterRef, Q, Subquery, Value, When
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.shortcuts import render

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import ModelViewSet
from django.http import HttpResponse

from django_filters.rest_framework import DjangoFilterBackend
from localflavor.us.us_states import STATE_CHOICES
from django.contrib.auth import get_user_model

from realtorx.custom_auth.tasks import (
    send_connection_request_email_to_agent2,
    send_follow_request,
    send_connection_request_email_to_agent3,
)
from realtorx.following.tasks import process_following_requests_from_phone
from realtorx.following.filters import (
    AgencyFilterBackend,
    FollowingFilterSet,
    FollowingFilterSetV2,
)
from realtorx.following.models import ConnectionsGroup, FollowingRequest
from realtorx.following.permissions import IsOwner
from realtorx.following.serializers import (
    FollowerSerializer,
    GroupBaseSerializer,
    GroupSerializer,
    FilterGroupBaseSerializer,
    AutoConnectionsSerializer,
)
from realtorx.houses.utils import get_point_from_address, get_address_from_point
from realtorx.utils.mixpanel import track_mixpanel_event
from realtorx.custom_auth.models import ApplicationUser
from django.db import connection
from django.conf import settings
import pytz


User = get_user_model()


class FollowingV1ViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = (
        ApplicationUser.objects.all().select_related("agency").order_by("full_name")
    )
    filterset_class = FollowingFilterSet
    serializer_class = FollowerSerializer
    lookup_field = "uuid"
    filter_backends = (
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
        AgencyFilterBackend,
    )
    search_fields = ("full_name",)
    ordering_fields = ["full_name"]

    def options(self, request, *args, **kwargs):
        """
        Reloaded for search field values fetching
        """
        response = super().options(request, *args, **kwargs)

        state_ser_field = self.serializer_class().fields["state"]
        state_ser_field.choices = [("", "All")] + list(STATE_CHOICES)

        response.data.update(
            {
                "search_options": {
                    "by_state": self.metadata_class().get_field_info(state_ser_field)[
                        "choices"
                    ]
                }
            },
        )

        return response

    def get_queryset(self):
        queryset = (
            super(FollowingV1ViewSet, self)
            .get_queryset()
            .exclude(id=self.request.user.id)
        )
        return queryset.exclude(
            Q(full_name="")
            | Q(user_type=ApplicationUser.TYPE_CHOICES.buyer)
            | Q(user_type=ApplicationUser.TYPE_CHOICES.trial)
        )

    def _get_annotate_queryset(self, queryset):
        following_request = FollowingRequest.objects.filter(
            Q(sender=self.request.user, recipient=OuterRef("id"))
            | Q(recipient=self.request.user, sender=OuterRef("id")),
        )
        queryset = queryset.annotate(
            following_status=Subquery(following_request.values("status")),
            _following_sender=Subquery(following_request.values("sender")),
            following_type=Case(
                When(_following_sender=F("id"), then=Value("in")),
                When(_following_sender=None, then=Value("none")),
                default=Value("out"),
                output_field=CharField(),
            ),
        ).exclude(id=self.request.user.id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if self.request.query_params.get("tab") == "company":
            if self.request.user.agency:
                queryset = queryset.filter(agency=self.request.user.agency)
            else:
                queryset = queryset.none()
        if self.request.query_params.get("tab") == "office":
            if self.request.user.agency and self.request.user.brokerage_phone_number:
                queryset = queryset.filter(
                    agency=self.request.user.agency,
                    brokerage_phone_number=self.request.user.brokerage_phone_number,
                )
            else:
                queryset = queryset.none()
        if self.request.query_params.get("following_type") == "none":
            self.request.user.search_count += 1
            self.request.user.save()

        page = self.paginate_queryset(queryset)
        if page is not None:
            user_ids = [user.id for user in page]
            queryset = queryset.filter(id__in=user_ids)
            queryset = self._get_annotate_queryset(queryset)
            serializer = self.get_serializer(queryset, many=True)
            return self.get_paginated_response(serializer.data)

        queryset = self._get_annotate_queryset(queryset)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["GET"],
        url_path="connect-time-limit",
        url_name="connect_time_limit",
    )
    def connect_time_limit(self, request, *args, **kwargs):
        now = datetime.now()
        if self.request.user.date_first_login:
            # Adding 30 days form user first time login date
            user_joined_date = self.request.user.date_first_login + timedelta(days=30)
            # Checking current date is bigger than user first login date after adding 30 days
            if now.date() > user_joined_date.date():
                data = {"connect_time_limit": False}
                return Response(data, status=status.HTTP_200_OK)
            else:
                data = {"connect_time_limit": True}
                return Response(data, status=status.HTTP_200_OK)
        else:
            return Response(
                "You can not call this api, as you haven't signed in even a single time.",
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["POST"])
    def follow(self, request, *args, **kwargs):

        sender = self.request.user
        recipient = self.get_object()

        # This code sends a connection request only only if no previous requests have been
        # sent between these two agents -- is this correct?
        if not FollowingRequest.objects.filter(
            Q(sender=sender, recipient=recipient)
            | Q(recipient=sender, sender=recipient)
        ).exists():

            agent_2_activity_threshold = datetime(2022, 3, 1, tzinfo=pytz.UTC)
            agent_2_skipped = False

            FollowingRequest.objects.create(sender=sender, recipient=recipient)

            if recipient.agent_type == "agent2":
                if recipient.houses.filter(
                    Q(created__gte=agent_2_activity_threshold)
                    | Q(modified__gte=agent_2_activity_threshold)
                ).exists():
                    send_connection_request_email_to_agent2.delay(
                        sender.id, recipient.id
                    )
                else:
                    agent_2_skipped = True

            elif recipient.agent_type == "agent3":
                send_connection_request_email_to_agent3.delay(sender.id, recipient.id)

            track_mixpanel_event(
                str(self.request.user.uuid),
                "new_connection_request_receiver",
                {
                    "sender_email": self.request.user.email,
                    "recipient_email": recipient.email,
                    "sender_uuid": str(self.request.user.uuid),
                    "recipient_uuid": str(recipient.uuid),
                    "sender_agent_type": self.request.user.agent_type,
                    "recipient_agent_type": recipient.agent_type,
                },
            )

            track_mixpanel_event(
                str(self.request.user.uuid),
                "new_connection_request_sender",
                {
                    "sender_email": self.request.user.email,
                    "recipient_email": [recipient.email],
                    "sender_uuid": str(self.request.user.uuid),
                    "recipient_uuid": [str(recipient.uuid)],
                    "sender_agent_type": self.request.user.agent_type,
                    "recipient_agent_type": [recipient.agent_type],
                    "agent_1_recipient_count": (
                        1 if recipient.agent_type == "agent1" else 0
                    ),
                    "agent_2_recipient_count": (
                        1
                        if recipient.agent_type == "agent2" and not agent_2_skipped
                        else 0
                    ),
                    "agent_2_recipient_skipped_count": (
                        1 if recipient.agent_type == "agent2" and agent_2_skipped else 0
                    ),
                    "agent_3_recipient_count": (
                        1 if recipient.agent_type == "agent3" else 0
                    ),
                    "case": "single connection",
                },
            )

            return Response(f"Connection request emailed to {recipient.full_name}")

        # Do nothing if these agents are already connected.
        if FollowingRequest.objects.filter(
            Q(sender=sender, recipient=recipient)
            | Q(recipient=sender, sender=recipient),
            status=FollowingRequest.REQUEST_STATUS.accepted,
        ).exists():
            return Response(
                data={
                    api_settings.NON_FIELD_ERRORS_KEY: [
                        _("Already following this user.")
                    ],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # If the receiver has already sent a connection request to the sender,
        # then accept the request -- the agents are now connected.
        try:
            existing_request = FollowingRequest.objects.get(
                recipient=sender,
                sender=recipient,
                status=FollowingRequest.REQUEST_STATUS.pending,
            )
            existing_request.follow()
            existing_request.save()
            track_mixpanel_event(
                str(self.request.user.uuid),
                "connection_request_accept",
                {
                    "sender_email": recipient.email,
                    "recipient_email": sender.email,
                    "sender_uuid": str(recipient.uuid),
                    "recipient_uuid": str(sender.uuid),
                },
            )

        except FollowingRequest.DoesNotExist:
            pass

        return Response()

    @action(detail=True, methods=["POST"])
    def unfollow(self, request, *args, **kwargs):
        user = self.get_object()
        for request in FollowingRequest.objects.filter(
            Q(sender=self.request.user, recipient=user)
            | Q(recipient=self.request.user, sender=user),
        ):
            groups_data = ConnectionsGroup.objects.filter(
                Q(owner=self.request.user, members=user)
                | Q(owner=user, members=self.request.user)
            )
            # Deleting 0 members connection group's when call unfollow
            if groups_data.exists():
                for members_user in groups_data:
                    if not members_user.members.count() > 1:
                        if (
                            members_user.owner == self.request.user
                            or members_user.members.get() == self.request.user
                        ) and members_user.members.count() == 1:
                            ConnectionsGroup.objects.filter(id=members_user.id).delete()
                    elif (
                        members_user.owner == self.request.user
                        and members_user.members.count() > 1
                    ):
                        members_user.members.remove(user)
                    elif (
                        members_user.owner == user and members_user.members.count() > 1
                    ):
                        members_user.members.remove(self.request.user)
            request.unfollow()

        return Response()


class MyConnectionV1ViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ApplicationUser.objects.all().order_by("full_name")
    filterset_class = FollowingFilterSet
    serializer_class = FollowerSerializer
    lookup_field = "uuid"
    filter_backends = (
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
        AgencyFilterBackend,
    )
    search_fields = ("full_name",)
    ordering_fields = ["full_name"]

    def get_queryset(self):
        queryset = self.queryset.exclude(id=self.request.user.id)
        return queryset.exclude(
            Q(full_name="")
            | Q(user_type=ApplicationUser.TYPE_CHOICES.buyer)
            | Q(user_type=ApplicationUser.TYPE_CHOICES.trial)
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if (
            self.request.query_params.get("following_status")
            == FollowingRequest.REQUEST_STATUS.pending
        ):
            if self.request.query_params.get("following_type") == "in":
                user_list = list(
                    FollowingRequest.objects.filter(
                        recipient=request.user,
                        status=FollowingRequest.REQUEST_STATUS.pending,
                    ).values_list("sender", flat=True)
                )
                queryset = queryset.filter(pk__in=user_list)
            elif self.request.query_params.get("following_type") == "out":
                user_list = list(
                    FollowingRequest.objects.filter(
                        sender=request.user,
                        status=FollowingRequest.REQUEST_STATUS.pending,
                    ).values_list("recipient", flat=True)
                )
                queryset = queryset.filter(pk__in=user_list)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        elif (
            self.request.query_params.get("following_status")
            == FollowingRequest.REQUEST_STATUS.accepted
        ):
            connected_user_list = list(
                FollowingRequest.objects.filter(
                    recipient=request.user,
                    status=FollowingRequest.REQUEST_STATUS.accepted,
                ).values_list("sender", flat=True)
            ) + list(
                FollowingRequest.objects.filter(
                    sender=request.user, status=FollowingRequest.REQUEST_STATUS.accepted
                ).values_list("recipient", flat=True)
            )
            queryset = queryset.filter(pk__in=connected_user_list)
            if self.request.query_params.get("tab") == "company":
                if self.request.user.agency:
                    queryset = queryset.filter(agency=self.request.user.agency)
                else:
                    queryset = queryset.none()
            if self.request.query_params.get("tab") == "office":
                if (
                    self.request.user.agency
                    and self.request.user.brokerage_phone_number
                ):
                    queryset = queryset.filter(
                        agency=self.request.user.agency,
                        brokerage_phone_number=self.request.user.brokerage_phone_number,
                    )
                else:
                    queryset = queryset.none()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


from rest_framework import pagination


class YourPagination(pagination.PageNumberPagination):

    def get_paginated_response(self, data, count):
        return Response(
            {
                "count": count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )


class DatabaseV1ViewSet(
    YourPagination,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ApplicationUser.objects.all().order_by("full_name")
    # filterset_class = FollowingFilterSet
    serializer_class = FollowerSerializer

    # lookup_field = 'uuid'
    # filter_backends = (
    #     DjangoFilterBackend,
    #     SearchFilter,
    #     OrderingFilter,
    #     AgencyFilterBackend,
    # )
    # search_fields = ('full_name',)
    # ordering_fields = ['full_name']

    # def get_queryset(self):
    #     connected_user_list = list(FollowingRequest.objects.filter(Q(status=FollowingRequest.REQUEST_STATUS.accepted) | Q(status=FollowingRequest.REQUEST_STATUS.pending), recipient=self.request.user).values_list("sender", flat=True)) + \
    #         list(FollowingRequest.objects.filter(Q(status=FollowingRequest.REQUEST_STATUS.accepted) | Q(status=FollowingRequest.REQUEST_STATUS.pending), sender=self.request.user).values_list("recipient", flat=True))
    #     connected_user_list.append(self.request.user.id)
    #     queryset = self.queryset.exclude(id__in=connected_user_list)
    #     return queryset.exclude(Q(full_name='') | Q(user_type=ApplicationUser.TYPE_CHOICES.buyer) | Q(
    #         user_type=ApplicationUser.TYPE_CHOICES.trial))

    def list(self, request, *args, **kwargs):
        # queryset = self.filter_queryset(self.get_queryset()).filter(is_superuser=False)

        sql_query = """where
        id not in (select sender_id from public.following_followingrequest where recipient_id={user_id})
        and id not in (select recipient_id from public.following_followingrequest where sender_id={user_id})
        and id not in ({user_id}) and full_name != '' and user_type != 'buyer' and user_type != 'trial' and is_superuser = 'false' """.format(
            user_id=request.user.id
        )

        if "state" in self.request.query_params:
            if (
                self.request.query_params.get("state") != ""
                and self.request.query_params.get("state") != "none"
            ):
                sql_query += """and state='{state}' """.format(
                    state=self.request.query_params.get("state")
                )

        if "county" in self.request.query_params:
            if (
                self.request.query_params.get("county") != ""
                and self.request.query_params.get("county") != "none"
            ):
                sql_query += """and county='{county}' """.format(
                    county=self.request.query_params.get("county")
                )

        if "city" in self.request.query_params:
            if (
                self.request.query_params.get("city") != ""
                and self.request.query_params.get("city") != "none"
            ):
                sql_query += """and city={city} """.format(
                    city="{" + self.request.query_params.get("city") + "}"
                )

        if "agency" in self.request.query_params:
            if (
                self.request.query_params.get("agency") != ""
                and self.request.query_params.get("agency") != "none"
            ):
                sql_query += """and agency_id={agency_id} """.format(
                    agency_id=self.request.query_params.get("agency")
                )

        if "search" in self.request.query_params:
            if (
                self.request.query_params.get("search") != ""
                and self.request.query_params.get("search") != "none"
            ):
                sql_query += """and full_name={full_name} """.format(
                    full_name=self.request.query_params.get("search")
                )

        order_by_query = """order by full_name"""

        select_sql = (
            """SELECT * FROM public.custom_auth_applicationuser """
            + sql_query
            + order_by_query
            + """ LIMIT 2000;"""
        )
        count_sql = (
            """SELECT count(*) FROM public.custom_auth_applicationuser """ + sql_query
        )

        with connection.cursor() as cursor:
            cursor.execute(count_sql)
            row = cursor.fetchone()
            count = row[0]

        queryset = ApplicationUser.objects.raw(select_sql)

        # count = queryset.count()
        # queryset = queryset[:1000]
        page = self.paginate_queryset(queryset, request=self.request)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data, count=count)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class FollowingV2ViewSet(FollowingV1ViewSet):
    filterset_class = FollowingFilterSetV2


class FollowingV3ViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = (
        ApplicationUser.objects.all().select_related("agency").order_by("full_name")
    )
    serializer_class = FollowerSerializer

    def get_queryset(self):
        return super().get_queryset().exclude(id=self.request.user.id)

    def list(self, request, *args, **kwargs):
        following_status = request.GET.get("following_status", None)
        geocode_address = request.GET.get("geocode_address", None)

        if following_status:
            q = FollowingRequest.objects.filter(
                Q(sender=self.request.user) | Q(recipient=self.request.user),
            )
            if following_status == "any":
                filter_kwarg = {"status__isnull": False}
            else:
                filter_kwarg = {"status": following_status}

            ids = []
            all_ids = q.filter(**filter_kwarg).values_list("sender_id", "recipient_id")
            for i in all_ids:
                ids = ids + list(i)

            if geocode_address:
                point = get_point_from_address(geocode_address)
                address = get_address_from_point(point)

                if address is not None:
                    state = address[4]
                    county = address[7]
                    city = address[3]
                    state = (
                        [item for item in STATE_CHOICES if state in item]
                        if state
                        else ""
                    )

            if len(tuple(set(ids))):
                following_status = tuple(set(ids))
                user_ids = []
                data = ApplicationUser.objects.filter(id__in=following_status)
                for user_id in data:
                    user_ids.append(user_id.id)
                following_status = tuple(set(user_ids))
            else:
                following_status = tuple([request.user.id])

            query_params = {
                "current_user": request.user.id,
                "following_status": following_status,
                "state": state[0][0] if state else "",
                "county": county,
                "county1": county.replace(" County", ""),  # update
                "city": "{" + city + "}",
                "category": request.GET.get("category", None),
                "baths_count": request.GET.get("baths_count", None),
                "carparks_count": request.GET.get("carparks_count", None),
                "bedrooms_count": request.GET.get("bedrooms_count", None),
                "price": (
                    0
                    if request.GET.get("price", None) in ["", None]
                    else request.GET.get("price", None)
                ),
                "property_type": "{" + request.GET.get("property_type", None) + "}",
            }
            # Added RAW SQL query for the suggested connection list in the house listing.

            sql_query = """ select DISTINCT "custom_auth_applicationuser"."id" , password,
                last_login, is_superuser, brokerage_phone_number, brokerage_address, brokerage_website, display_realtor_logo,
                display_fair_housing_logo, schedule_id, email_notifications_enabled, avatar, phone, verified_user, uuid, username,
                full_name, first_name,last_name, email, "custom_auth_applicationuser"."state", "custom_auth_applicationuser"."county",
                "custom_auth_applicationuser"."city", agency_id, is_staff, is_active, date_joined, date_first_login, first_login,
                send_email_with_temp_password,temp_password, show_splash_screen_login, show_splash_screen_house,
                show_splash_screen_search, "agencies_agency"."id", "agencies_agency"."name","agencies_agency"."about"
                FROM "custom_auth_applicationuser" LEFT OUTER JOIN "houses_savedfilter"on
                ("custom_auth_applicationuser"."id" = "houses_savedfilter"."user_id") LEFT OUTER JOIN "houses_savedfilter" T3 ON
                ("custom_auth_applicationuser"."id" = T3."user_id") INNER JOIN "houses_savedfilter" T5 on
                ("custom_auth_applicationuser"."id" = T5."user_id") LEFT OUTER JOIN "agencies_agency" on
                ("custom_auth_applicationuser"."agency_id" = "agencies_agency"."id")
                WHERE (NOT ("custom_auth_applicationuser"."id" = %(current_user)s)
                AND  "custom_auth_applicationuser"."id" IN %(following_status)s
                AND ("houses_savedfilter"."state" = %(state)s OR UPPER("houses_savedfilter"."state"::text) = UPPER('')
                OR "houses_savedfilter"."state" IS NULL OR UPPER("houses_savedfilter"."state"::text) = UPPER('ALL'))
                AND ((UPPER(T3."county"::text) = UPPER(%(county)s) OR UPPER(T3."county"::text) = UPPER(%(county1)s))
                OR UPPER(T3."county"::text) = UPPER('') OR T3."county" IS NULL OR UPPER(T3."county"::text) = UPPER('ALL'))
                AND (T3."city" && %(city)s::varchar(100)[] OR T3."city" IS NULL OR T3."city" = '{}')
                AND T5."action"::text LIKE %(category)s
                AND (T5."baths_count_min" <= %(baths_count)s OR T5."baths_count_min" IS NULL)
                AND (T5."carparks_count_min" <= %(carparks_count)s OR T5."carparks_count_min" IS NULL)
                AND (T5."bedrooms_count_min" <= %(bedrooms_count)s OR T5."bedrooms_count_min" IS NULL)
                AND (T5."house_types" @> %(property_type)s::varchar(30)[] OR T5."house_types" = '{}' OR T5."house_types" IS NULL)
                AND (T5."price_min" <= %(price)s OR T5."price_min" IS NULL)"""

            price = (
                0
                if request.GET.get("price", None) in ["", None]
                else request.GET.get("price", None)
            )
            if int(price) <= settings.FILTER_MAX_PRICE:
                sql_query += (
                    """AND (T5."price_max" >= %(price)s OR T5."price_max" IS NULL)"""
                )

            allow_large_dogs = request.GET.get("allow_large_dogs", None)
            if allow_large_dogs:
                large_dogs = "yes" if allow_large_dogs in ["yes", "may_be"] else "no"
                query_params.update({"large_dogs": large_dogs})
                sql_query += """AND (T5."allow_large_dogs"::text = %(large_dogs)s OR T5."allow_large_dogs" IS NULL)"""

            allow_small_dogs = request.GET.get("allow_small_dogs", None)
            if allow_small_dogs:
                small_dogs = "yes" if allow_small_dogs in ["yes", "may_be"] else "no"
                query_params.update({"small_dogs": small_dogs})
                sql_query += """AND (T5."allow_small_dogs"::text = %(small_dogs)s OR T5."allow_small_dogs" IS NULL)"""

            allow_cats = request.GET.get("allow_cats", None)
            if allow_cats:
                cats = "yes" if allow_cats in ["yes", "may_be"] else "no"
                query_params.update({"cats": cats})
                sql_query += """AND (T5."allow_cats"::text = %(cats)s OR T5."allow_cats" IS NULL)"""

            internal_listing = eval(
                request.GET.get("internal_listing", "false").title()
            )
            if internal_listing:
                agency = request.user.agency.name if request.user.agency else None
                query_params.update({"agency": agency})
                sql_query += """AND (agencies_agency."name"::text = %(agency)s) """

            internal_office = eval(request.GET.get("internal_office", "false").title())
            if internal_office:
                agency = request.user.agency.name if request.user.agency else None
                broker_phone = (
                    request.user.brokerage_phone_number
                    if request.user.brokerage_phone_number
                    else None
                )
                query_params.update({"agency": agency, "broker_phone": broker_phone})
                sql_query += """AND (agencies_agency."name"::text = %(agency)s AND
                custom_auth_applicationuser."brokerage_phone_number"::text = %(broker_phone)s) """

            sql_query += """) ORDER BY full_name ASC"""

            queryset = ApplicationUser.objects.raw(sql_query, query_params)
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

    @action(
        detail=False,
        methods=["GET"],
        url_path="trial-listing",
        url_name="trial_listing",
    )
    def trial_listing(self, request, *args, **kwargs):
        queryset = self.get_queryset().filter(agency__name="AgentLoop HQ")
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class GroupViewSet(ModelViewSet):
    """
    View create, edit, and delete ConnectionsGroup.
    """

    queryset = ConnectionsGroup.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (IsAuthenticated, IsOwner)
    filter_backends = (OrderingFilter,)
    ordering = ("name",)

    def get_serializer_class(self):
        if self.action in ["list", "create"]:
            return GroupBaseSerializer

        return self.serializer_class

    def get_queryset(self):
        return ConnectionsGroup.objects.filter(owner=self.request.user)

    def list(self, request, *args, **kwargs):
        response = super(GroupViewSet, self).list(request, *args, **kwargs)
        if "results" in response.data:
            # adding temporary auto group for company and internal office
            if self.request.user.agency:
                broker_name = self.request.user.agency.name + " - Internal Office"
                if not ConnectionsGroup.objects.filter(
                    owner=self.request.user, name=self.request.user.agency.name
                ).exists():
                    # adding temporary auto group for company
                    response.data["count"] = len(response.data["results"]) + 1
                    response.data["results"] = response.data["results"] + [
                        {
                            "id": 0,
                            "name": self.request.user.agency.name,
                            "members": [],
                            "group_base": "Company",
                        }
                    ]
                if not ConnectionsGroup.objects.filter(
                    owner=self.request.user, name=broker_name
                ).exists():
                    # adding temporary auto group for company internal office
                    response.data["count"] = len(response.data["results"]) + 1
                    response.data["results"] = response.data["results"] + [
                        {
                            "id": 0,
                            "name": broker_name,
                            "members": [],
                            "group_base": "Internal",
                        }
                    ]

        return response

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        if len(serializer.validated_data["members"]) > 0:
            serializer.validated_data["members"] = ApplicationUser.objects.filter(
                uuid__in=serializer.validated_data["members"]
            ).values_list("id", flat=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        else:
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class GroupV2ViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    View ConnectionsGroup.
    """

    queryset = ConnectionsGroup.objects.all()
    serializer_class = GroupBaseSerializer
    permission_classes = (IsAuthenticated, IsOwner)
    filter_backends = (OrderingFilter,)
    ordering = ("name",)

    def get_queryset(self):
        return ConnectionsGroup.objects.filter(owner=self.request.user)

    def list(self, request, *args, **kwargs):
        response = super(GroupV2ViewSet, self).list(request, *args, **kwargs)
        with_all = request.query_params.get("with_all")
        page = request.query_params.get("page")
        if (
            with_all is not None
            and with_all.lower() in ("1", "true", "yes")
            and (page == "1" or page is None)
        ):
            if "results" in response.data:
                # adding temporary auto group for company and internal office
                if self.request.user.agency:
                    broker_name = self.request.user.agency.name + " - Internal Office"
                    if not ConnectionsGroup.objects.filter(
                        owner=self.request.user, name=self.request.user.agency.name
                    ).exists():
                        # adding temporary auto group for company
                        response.data["count"] = len(response.data["results"]) + 1
                        response.data["results"] = response.data["results"] + [
                            {
                                "id": 0,
                                "name": self.request.user.agency.name,
                                "members": [],
                                "group_base": "Company",
                            }
                        ]
                    if not ConnectionsGroup.objects.filter(
                        owner=self.request.user, name=broker_name
                    ).exists():
                        # adding temporary auto group for company internal office
                        response.data["count"] = len(response.data["results"]) + 1
                        response.data["results"] = response.data["results"] + [
                            {
                                "id": 0,
                                "name": broker_name,
                                "members": [],
                                "group_base": "Internal",
                            }
                        ]
            else:
                # adding temporary auto group for company and internal office
                if self.request.user.agency:
                    broker_name = self.request.user.agency.name + " - Internal Office"
                    if not ConnectionsGroup.objects.filter(
                        owner=self.request.user, name=self.request.user.agency.name
                    ).exists():
                        # adding temporary auto group for company
                        response.data = response.data + [
                            {
                                "id": 0,
                                "name": self.request.user.agency.name,
                                "members": [],
                                "group_base": "Company",
                            }
                        ]
                    if not ConnectionsGroup.objects.filter(
                        owner=self.request.user, name=broker_name
                    ).exists():
                        # adding temporary auto group for company internal office
                        response.data = response.data + [
                            {
                                "id": 0,
                                "name": broker_name,
                                "members": [],
                                "group_base": "Internal",
                            }
                        ]
        return response


class FilterGroupViewSet(ModelViewSet):
    """
    View create, edit, and delete ConnectionsGroup.
    """

    queryset = ConnectionsGroup.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (IsAuthenticated, IsOwner)
    filter_backends = (OrderingFilter,)
    ordering = ("name",)

    def get_serializer_class(self):
        if self.action in ["list"]:
            return FilterGroupBaseSerializer

        return self.serializer_class

    def get_queryset(self):
        return ConnectionsGroup.objects.filter(owner=self.request.user)


# class AcceptRenderTemplate(View):
#     pass


class AcceptRenderTemplate(View):
    def get(self, request, uuid):
        try:
            user = User.objects.get(uuid=uuid)
            data = {"full_name": user.full_name, "temp_password": user.temp_password}
        except User.DoesNotExist:
            return render(
                request, "email/accept_template.html", {"user": "no data found"}
            )
        return render(request, "email/accept_template.html", data)


class UnsubscribeEmail(View):
    def get(self, request, uuid):
        template_message = "You have successfully unsubscribed from our mailing list."
        try:
            user = User.objects.get(uuid=uuid)
            if not user.connection_email_unsubscribe:
                user.connection_email_unsubscribe = True
                user.save()

                track_mixpanel_event(
                    str(user.uuid),
                    "email_unsubscribe",
                    {
                        "email": user.email,
                        "phone": str(user.phone),
                        "full_name": user.full_name,
                        "email_unsubscribed": user.connection_email_unsubscribe,
                    },
                )
            else:
                track_mixpanel_event(
                    str(user.uuid),
                    "duplicate_email_unsubscribe",
                    {
                        "email": user.email,
                        "phone": str(user.phone),
                        "full_name": user.full_name,
                        "email_unsubscribed": user.connection_email_unsubscribe,
                    },
                )

                template_message = (
                    "You have already unsubscribed from our mailing list."
                )
        except User.DoesNotExist:
            template_message = "User does not exist on Agentloop!"

        return render(request, "unsubscribe.html", {"message": template_message})


class FollowingV4ViewSet(FollowingV1ViewSet):
    @action(
        methods=["POST"],
        url_name="follow_list_request",
        url_path="follow-list-request",
        detail=False,
    )
    def follow_list_request(self, request, *args, **kwargs):
        """
        Called when an agent clicks on "Connect to all" after searching the database
        """

        queryset = list(
            self.filter_queryset(self.get_queryset()).values_list("id", flat=True)
        )

        send_follow_request.delay(queryset, request.user.id)

        return Response(f"Sent follow request to {len(queryset)} matching agents.")

    def list(self, request, *args, **kwargs):
        now = datetime.now()
        if self.request.user.date_first_login:
            if self.request.user.agency:
                # Adding 30 days form user first time login date
                user_joined_date = self.request.user.date_first_login + timedelta(
                    days=30
                )
                # Checking current date is smaller than user first login date after adding 30 days
                if not now.date() > user_joined_date.date():
                    state = request.GET.get("state", None)
                    county = request.GET.get("county", None)
                    agency = request.GET.get("agency", None)
                    user_name = request.GET.get("search", None)
                    if not (
                        (state is not None and state == self.request.user.state)
                        and (
                            user_name is not None
                            or (
                                county is not None
                                and county == self.request.user.county[0]
                            )
                            or (
                                agency is not None
                                and int(agency) == self.request.user.agency.id
                            )
                        )
                    ):
                        return Response(
                            "Your connections are limited during first 30 days!",
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                response_data = FollowingV1ViewSet.list(self, request, *args, **kwargs)
                # self.request.user.search_count += 1
                # self.request.user.save()
                return Response(response_data.data)
            else:
                return Response(
                    "Please update your profile so you can connect with agents in your area!",
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                "You can not call this api, as you haven't signed in even a single time.",
                status=status.HTTP_400_BAD_REQUEST,
            )


def remove_group(request):
    groups_data = ConnectionsGroup.objects.all()
    for item in groups_data:
        if item.members.count() == 0:
            ConnectionsGroup.objects.filter(id=item.id).delete()
    return HttpResponse("Successfully", status=status.HTTP_200_OK)


class FollowingV5ViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = (
        ApplicationUser.objects.all().select_related("agency").order_by("full_name")
    )
    serializer_class = FollowerSerializer

    def get_queryset(self):
        return super().get_queryset().exclude(id=self.request.user.id)

    def sql_query_filter(self, request, query_params, query):
        price = (
            0
            if request.GET.get("price", None) in ["", None]
            else request.GET.get("price", None)
        )
        if int(price) <= settings.FILTER_MAX_PRICE:
            query += """AND (hs."price_max" >= %(price)s OR hs."price_max" IS NULL)"""

        allow_large_dogs = request.GET.get("allow_large_dogs", None)
        if allow_large_dogs:
            large_dogs = "yes" if allow_large_dogs in ["yes", "may_be"] else "no"
            query_params.update({"large_dogs": large_dogs})
            query += """AND (hs."allow_large_dogs"::text = %(large_dogs)s OR hs."allow_large_dogs" IS NULL)"""

        allow_small_dogs = request.GET.get("allow_small_dogs", None)
        if allow_small_dogs:
            small_dogs = "yes" if allow_small_dogs in ["yes", "may_be"] else "no"
            query_params.update({"small_dogs": small_dogs})
            query += """AND (hs."allow_small_dogs"::text = %(small_dogs)s OR hs."allow_small_dogs" IS NULL)"""

        allow_cats = request.GET.get("allow_cats", None)
        if allow_cats:
            cats = "yes" if allow_cats in ["yes", "may_be"] else "no"
            query_params.update({"cats": cats})
            query += (
                """AND (hs."allow_cats"::text = %(cats)s OR hs."allow_cats" IS NULL)"""
            )

        internal_listing = eval(request.GET.get("internal_listing", "false").title())
        if internal_listing:
            agency = request.user.agency.name if request.user.agency else None
            query_params.update({"agency": agency})
            query += """AND (agencies_agency."name"::text = %(agency)s) """

        internal_office = eval(request.GET.get("internal_office", "false").title())
        if internal_office:
            agency = request.user.agency.name if request.user.agency else None
            broker_phone = (
                request.user.brokerage_phone_number
                if request.user.brokerage_phone_number
                else None
            )
            query_params.update({"agency": agency, "broker_phone": broker_phone})
            query += """AND (agencies_agency."name"::text = %(agency)s AND
                        custom_auth_applicationuser."brokerage_phone_number"::text = %(broker_phone)s) """

        return query

    def list(self, request, *args, **kwargs):
        geocode_address = request.GET.get("geocode_address", None)

        user_data = (
            ApplicationUser.objects.filter(is_superuser=False)
            .exclude(
                Q(is_active=False)
                | Q(id=self.request.user.id)
                | Q(user_type=ApplicationUser.TYPE_CHOICES.trial)
            )
            .values_list("id", flat=True)
        )
        if user_data:
            following_status = tuple(set(user_data))

        count_value = 0
        if geocode_address:
            point = get_point_from_address(geocode_address)
            address = get_address_from_point(point)

            if address is not None:
                state = address[4]
                county = address[7]
                city = address[3]
                state = (
                    [item for item in STATE_CHOICES if state in item] if state else ""
                )

                query_params = {
                    "current_user": request.user.id,
                    "following_status": following_status,
                    "state": state[0][0] if state else "",
                    "county": county,
                    "county1": county.replace(" County", ""),  # update
                    "city": "{" + city + "}",
                    "category": request.GET.get("category", None),
                    "baths_count": request.GET.get("baths_count", None),
                    "carparks_count": request.GET.get("carparks_count", None),
                    "bedrooms_count": request.GET.get("bedrooms_count", None),
                    "price": (
                        0
                        if request.GET.get("price", None) in ["", None]
                        else request.GET.get("price", None)
                    ),
                    "property_type": "{" + request.GET.get("property_type", None) + "}",
                }
                # Added RAW SQL query for the suggested connection list in the house listing.

                sql_query = """ select count(DISTINCT("custom_auth_applicationuser"."id")) as "users"
                FROM "custom_auth_applicationuser" LEFT OUTER JOIN "houses_savedfilter" hs on
                ("custom_auth_applicationuser"."id" = hs."user_id") LEFT OUTER JOIN "agencies_agency" on
                ("custom_auth_applicationuser"."agency_id" = "agencies_agency"."id")
                WHERE (NOT ("custom_auth_applicationuser"."id" = %(current_user)s)
                AND  "custom_auth_applicationuser"."id" IN %(following_status)s
                AND (hs."state" = %(state)s OR UPPER(hs."state"::text) = UPPER('')
                OR hs."state" IS NULL OR UPPER(hs."state"::text) = UPPER('ALL'))
                AND ((UPPER(hs."county"::text) = UPPER(%(county)s) OR UPPER(hs."county"::text) = UPPER(%(county1)s))
                OR UPPER(hs."county"::text) = UPPER('') OR hs."county" IS NULL OR UPPER(hs."county"::text) = UPPER('ALL'))
                AND (hs."city" && %(city)s::varchar(100)[] OR hs."city" IS NULL OR hs."city" = '{}')
                AND hs."action"::text LIKE %(category)s
                AND (hs."baths_count_min" <= %(baths_count)s OR hs."baths_count_min" IS NULL)
                AND (hs."carparks_count_min" <= %(carparks_count)s OR hs."carparks_count_min" IS NULL)
                AND (hs."bedrooms_count_min" <= %(bedrooms_count)s OR hs."bedrooms_count_min" IS NULL)
                AND (hs."house_types" @> %(property_type)s::varchar(30)[] OR hs."house_types" = '{}' OR hs."house_types" IS NULL)
                AND (hs."price_min" <= %(price)s OR hs."price_min" IS NULL)"""

                sql_query = self.sql_query_filter(request, query_params, sql_query)
                sql_query += """)"""

                with connection.cursor() as cursor:
                    cursor.execute(sql_query, query_params)
                    row = cursor.fetchone()
                    count_value = row[0]

        return Response({"count": count_value}, status=status.HTTP_200_OK)


@api_view(["GET"])
def create_following_requests_from_number(request):
    serilizer = AutoConnectionsSerializer(data=request.query_params)
    serilizer.is_valid(raise_exception=True)
    process_following_requests_from_phone.delay(
        serilizer.data["phone_number_list"], request.user.id
    )
    return Response("Your connection requests are being processed.")
