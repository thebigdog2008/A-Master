import base64
import json
from django.db.models import (
    Exists,
    OuterRef,
    Prefetch,
    Q,
    QuerySet,
    Case,
    When,
    IntegerField,
)
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404

from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.views import APIView

from django_filters.rest_framework import DjangoFilterBackend
from unicef_restlib.views import MultiSerializerViewSetMixin

try:
    from weasyprint import HTML
except OSError:
    pass
from realtorx.attachments.models import Attachment
from realtorx.custom_auth.models import ApplicationUser
from realtorx.houses.filters import (
    HousesFilterSet,
    HouseStatusFilterBackend,
    InterestFilterBackend,
    SavedFiltersFilterBackend,
    HouseInterestFilterBackend,
)
from realtorx.houses.models import FloorPlan, House, HousePhoto, Interest
from realtorx.houses.permissions import IsHouseCreator, IsNotHouseCreator
from realtorx.houses.serializers.house import owned as my_serializers
from realtorx.houses.serializers.house import owned_v2 as my_serializers_v2
from realtorx.houses.serializers.house import owned_v3 as my_serializers_v3
from realtorx.houses.serializers.house import public as all_serializers
from realtorx.houses.serializers.house import public_v2 as all_serializers_v2
from realtorx.houses.serializers.house import search as search_serializers
from realtorx.houses.serializers.house import search_v2 as search_serializers_v2
from realtorx.houses.serializers.house.base import CheckHouseDataSerializer
from realtorx.houses.serializers.interest import InterestSerializer
from realtorx.permissions.views import SimplePermittedFSMTransitionActionMixin
from realtorx.photo.api import BasePhotosViewSet
from realtorx.utils.mixpanel import track_mixpanel_event
from realtorx.utils.pagination import SwitchableCursorPaginationViewMixin
from datetime import datetime, timedelta, time
import pytz
from realtorx.push_notification.handlers import PushNotification


class SearchHousesViewSet(
    SwitchableCursorPaginationViewMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = (
        House.objects.filter(
            status=House.HOUSE_STATUSES.published,
        )
        .select_related("user")
        .prefetch_related(
            Prefetch("photos", HousePhoto.objects.order_by("-is_main", "added_at"))
        )
    )
    serializer_class = search_serializers.HouseSerializer
    filter_backends = (SavedFiltersFilterBackend,)

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        return (
            queryset.annotate(
                interest_exists=Exists(
                    Interest.objects.filter(
                        house=OuterRef("id"), user=self.request.user
                    ).values("interest"),
                ),
            )
            .filter(
                Q(whitelist=self.request.user),
                user__following=self.request.user,
                interest_exists=False,
            )
            .distinct()
        )


class SearchHousesV2ViewSet(
    SwitchableCursorPaginationViewMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = (
        House.objects.filter(
            status=House.HOUSE_STATUSES.published,
        )
        .select_related("user")
        .prefetch_related(
            Prefetch("photos", HousePhoto.objects.order_by("-is_main", "added_at"))
        )
        .order_by("-created")
    )
    serializer_class = search_serializers_v2.HouseSerializer
    filter_backends = (SavedFiltersFilterBackend,)

    def get_queryset(self) -> QuerySet:
        queryset = (
            super()
            .get_queryset()
            .exclude(user=self.request.user)
            .exclude(main_photo__isnull=True)
            .exclude(main_photo__exact="")
        )  # finds all published houses not created by the user
        if self.request.user.user_type == ApplicationUser.TYPE_CHOICES.trial:
            listing_queryset = (
                queryset.filter(listing_type=House.LISTING_TYPES.listhublisting)
                .annotate(
                    interest_exists=Exists(
                        Interest.objects.filter(
                            house=OuterRef("id"), user=self.request.user
                        ).values("interest"),
                    ),
                )
                .filter(
                    interest_exists=False,
                )
                .distinct()
            )
            # queryset = queryset.exclude(listing_type=House.LISTING_TYPES.listhublisting).annotate(
            #     interest_exists=Exists(
            #         Interest.objects.filter(house=OuterRef('id'), user=self.request.user).values('interest'),
            #     ),
            # ).filter(
            #     Q(whitelist=self.request.user),
            #     interest_exists=False,
            # ).distinct()
            # return queryset | list_hub_house
        else:
            listing_queryset = (
                queryset.annotate(
                    interest_exists=Exists(
                        Interest.objects.filter(
                            house=OuterRef("id"), user=self.request.user
                        ).values("interest"),
                    ),
                )
                .filter(
                    # Q(whitelist=self.request.user),
                    interest_exists=False,
                )
                .distinct()
            )

        return listing_queryset

    def list(self, request, *args, **kwargs):
        base_queryset = (
            self.get_queryset()
        )  # houses not created by the user in which they have been not been interested yet
        queryset = self.filter_queryset(base_queryset)  # applies filter from the url
        # house_queryset = House.objects.filter(user=request.user).count() # gets the count of the houses created by the user
        # demo_data = House.objects.annotate(
        #     interest_exists=Exists(
        #         Interest.objects.filter(house=OuterRef('id'), user=self.request.user).values('interest'),
        #     ), ).filter(Q(is_demo_property=True, interest_exists=False)).distinct()

        if request.query_params.get("apply_saved_filters") == "all":
            past_120_days_datetime = datetime.now(timezone.utc) - timedelta(
                days=House.LISTINGS_DAYS_LIMIT
            )
            queryset = queryset.filter(modified__gte=past_120_days_datetime)

        # from queryset_sequence import QuerySetSequence
        # if base_queryset.count() == 0 and request.user.interests.count() == 0 and house_queryset == 0:
        #     result_list = QuerySetSequence(queryset, demo_data)
        # elif request.user.interests.filter(
        #     house__is_demo_property=False).count() == 0 and house_queryset == 0 and base_queryset.count() == 0:
        #     result_list = QuerySetSequence(queryset, demo_data)
        # else:
        #     result_list = queryset

        # if self.request.user.agency:
        #     print("user has agency")
        #     if self.request.user.agency.name == 'AgentLoop HQ':
        #         print("agency is AgentLoop HQ")
        #         test_listing_queryset = self.queryset.filter(listing_type='triallisting').annotate(
        #             interest_exists=Exists(
        #                 Interest.objects.filter(house=OuterRef('id'), user=self.request.user).values('interest'),
        #             ),
        #         ).filter(
        #             # Q(whitelist=self.request.user),
        #             interest_exists=False,
        #         ).distinct()
        #         print("test_listing_queryset", test_listing_queryset)
        #         result_list = result_list | test_listing_queryset

        # order manually by listing_type
        # amazinglisting=Amazing Listing, minutelisting=Sneakpeek Listing,  and listhublisting=Listhub Listing
        result_list = queryset.annotate(
            listorder=Case(
                When(listing_type="amazinglisting", then=1),
                When(listing_type="minutelisting", then=2),
                When(listing_type="listhublisting", then=3),
                output_field=IntegerField(),
            )
        ).order_by("listorder", "-modified")

        page = self.paginate_queryset(result_list)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            if Interest.objects.filter(user=self.request.user).count() > 2:
                return self.get_paginated_response(serializer.data)
            show_count = 4
            for i in range(len(serializer.data)):
                serializer.data[i]["show_swipes"] = (
                    serializer.data[i]["show_swipes"] + show_count
                )
                show_count = show_count + 1

            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(result_list, many=True)
        return Response(serializer.data)

    @action(
        methods=["GET"],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path="show-swipes",
        url_name="show_swipes",
    )
    def show_swipes(self, request, *args, **kwargs):
        if Interest.objects.filter(user=self.request.user).count() > 3:
            return Response({"show_swipes": False})
        else:
            return Response({"show_swipes": True})

    @action(
        methods=["GET"],
        detail=False,
        permission_classes=[AllowAny],
        url_path="home-video",
        url_name="home_video",
    )
    def home_video(self, request, *args, **kwargs):
        if HomeVideo.objects.all().count() > 0:
            video = HomeVideo.objects.all()
            home_video_serializer = HomeVideoSerializer(video, many=True)
            return Response(home_video_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response([{"video": ""}], status=status.HTTP_200_OK)


class CheckHouseDataActionMixin(object):
    @action(
        detail=False,
        methods=["POST"],
        url_name="check_house_data",
        url_path="check-house-data",
        permission_classes=[IsAuthenticated],
    )
    def check_house_data(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response()


class MyHousesViewSet(
    CheckHouseDataActionMixin,
    SimplePermittedFSMTransitionActionMixin,
    SwitchableCursorPaginationViewMixin,
    MultiSerializerViewSetMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = House.objects.all()
    serializer_class = my_serializers.HouseDetailSerializer
    filter_backends = (
        HouseStatusFilterBackend,
        OrderingFilter,
    )
    serializer_action_classes = {
        "list": my_serializers.HouseListSerializer,
        "check_house_data": CheckHouseDataSerializer,
    }
    permission_classes = [IsAuthenticated, IsHouseCreator]
    transition_permission_classes = {
        "publish": [IsHouseCreator],
        "archive": [IsHouseCreator],
    }
    ordering = "-created"

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user).select_related(
            "user", "user__agency"
        )
        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                "whitelist",
                Prefetch("photos", HousePhoto.objects.order_by("-is_main", "added_at")),
            )
        return queryset


class MyHousesV2ViewSet(
    CheckHouseDataActionMixin,
    SimplePermittedFSMTransitionActionMixin,
    SwitchableCursorPaginationViewMixin,
    MultiSerializerViewSetMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = House.objects.all()
    serializer_class = my_serializers_v2.HouseDetailSerializer
    filter_backends = (
        HouseStatusFilterBackend,
        OrderingFilter,
    )
    serializer_action_classes = {
        "list": my_serializers_v2.HouseListSerializer,
        "check_house_data": CheckHouseDataSerializer,
    }
    permission_classes = [IsAuthenticated, IsHouseCreator]
    transition_permission_classes = {
        "publish": [IsHouseCreator],
        "archive": [IsHouseCreator],
    }
    ordering = "-created"

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user).prefetch_related(
            "appointments"
        )
        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                "whitelist",
                Prefetch("photos", HousePhoto.objects.order_by("-is_main", "added_at")),
            )
        return queryset

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        response.data.get("appointments").clear()
        # removed appointments from response to fix the date format issue in IOS.
        # Data corrupted: Date string does not match format expected by formatter
        return response

    @action(
        detail=True,
        methods=["PATCH"],
        url_name="set_video",
        url_path="set-video",
        permission_classes=[IsAuthenticated, IsHouseCreator],
    )
    def set_video(self, request, *args, **kwargs):
        house = self.get_object()
        video = self.request.data.get("video")
        video_thumb = self.request.data.get("video_thumb")
        if self.request.data.get("is_delete"):
            house.video = None
            house.video_thumb = None
            house.save(update_fields=["video", "video_thumb"])
        else:
            if video:
                data = {"video": video}
                serializer = my_serializers_v2.HouseVideoSerializer(
                    house, data=data, partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
            if video_thumb:
                data = {"video_thumb": video_thumb}
                serializer = my_serializers_v2.HouseVideoSerializer(
                    house, data=data, partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()

        return Response({"status": "True"}, status=status.HTTP_200_OK)


class MyHousesV3ViewSet(
    CheckHouseDataActionMixin,
    SimplePermittedFSMTransitionActionMixin,
    SwitchableCursorPaginationViewMixin,
    MultiSerializerViewSetMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = House.objects.all()
    serializer_class = my_serializers_v3.HouseDetailSerializer
    filter_backends = (
        HouseStatusFilterBackend,
        OrderingFilter,
    )
    serializer_action_classes = {
        "list": my_serializers_v3.HouseListSerializer,
        "check_house_data": CheckHouseDataSerializer,
    }
    permission_classes = [IsAuthenticated, IsHouseCreator]
    transition_permission_classes = {
        "publish": [IsHouseCreator],
        "archive": [IsHouseCreator],
    }
    ordering_fields = ["day_interested", "created", "modified"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        if (
            "potential_count" in serializer.validated_data
            and serializer.validated_data["potential_count"] == "true"
        ):
            return Response(
                {
                    "count": serializer.validated_data["count"],
                    "is_house_notifiable": serializer.validated_data[
                        "is_house_notifiable"
                    ],
                },
                status=status.HTTP_200_OK,
            )
        else:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=headers
            )

    def list(self, request, *args, **kwargs):

        queryset = self.filter_queryset(self.get_queryset())

        queryset = queryset.order_by("-day_interested", "-modified")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .exclude(main_photo__isnull=True)
            .exclude(main_photo__exact="")
        )
        queryset = queryset.filter(user=self.request.user).prefetch_related(
            "appointments"
        )
        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                "whitelist",
                Prefetch("photos", HousePhoto.objects.order_by("-is_main", "added_at")),
            )
        return queryset.with_day_interested_users_amount()

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        data = serializer.data
        data["whitelist"] = []

        # Get users who have given not interest on the property
        not_interest_user_ids = list(
            Interest.objects.filter(
                house=self.get_object(), interest=Interest.INTEREST_NO
            ).values_list("user_id", flat=True)
        )

        # Get potential users count for the property.
        data["count"] = len(
            [
                user_id
                for user_id in data["sent_to_users"]
                if user_id not in not_interest_user_ids
            ]
        )

        return Response(data=data, status=status.HTTP_200_OK)


class HousePublicActionsViewMixin(object):
    @action(
        detail=True,
        methods=["POST"],
        url_name="set_interest",
        url_path="set-interest",
        permission_classes=[IsAuthenticated, IsNotHouseCreator],
    )
    def set_interest(self, request, *args, **kwargs):
        serializer = InterestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        house_instance = self.get_object()
        Interest.objects.update_or_create(
            house=house_instance,
            user=request.user,
            defaults=serializer.validated_data,
        )
        event_key = (
            "property_interest"
            if serializer.validated_data["interest"] == 2
            else "property_not_interested"
        )
        track_mixpanel_event(
            str(request.user.uuid),
            event_key,
            {
                "email": request.user.email,
                "phone": str(request.user.phone),
                "full_name": request.user.full_name,
                "house_address": house_instance.address,
                "house_mls_number": house_instance.mls_number,
                "created_from_listhub": str(house_instance.created_from_listhub),
                "type_of_interest": (
                    "Interested"
                    if serializer.validated_data["interest"] == 2
                    else "Not interested"
                ),
            },
        )
        return Response()

    @action(
        detail=True,
        methods=["POST"],
        url_name="set_undo",
        url_path="set-undo",
        permission_classes=[IsAuthenticated, IsNotHouseCreator],
    )
    def set_undo(self, request, *args, **kwargs):
        """
        define this method to delete not interested house entry and set the house in the unset list
        """
        interest_obj = get_object_or_404(
            Interest, house=self.get_object(), user=request.user
        )
        interest_obj.delete()

        return Response()

    @action(
        detail=True,
        methods=["GET"],
        url_name="get_interest",
        url_path="get-interest",
        permission_classes=[IsAuthenticated],
    )
    def get_interest(self, request, *args, **kwargs):
        return Response(
            data=InterestSerializer(
                instance=Interest.objects.filter(
                    user=self.request.user, house=self.get_object()
                ).first(),
            ).data,
        )

    @action(
        detail=False,
        methods=["GET"],
        url_name="get_latest_interest",
        url_path="get-latest-interest",
        permission_classes=[IsAuthenticated],
    )
    def get_latest_interest(self, request, *args, **kwargs):
        if datetime.now().strftime("%A") == "Monday":
            start_date = pytz.utc.localize(
                datetime.combine((datetime.now().date() - timedelta(2)), time())
            )
            end_date = pytz.utc.localize(
                datetime.combine((start_date.date() + timedelta(1)), time(23, 59, 59))
            )
        else:
            start_date = pytz.utc.localize(
                datetime.combine((datetime.now().date() - timedelta(1)), time())
            )
            end_date = pytz.utc.localize(datetime.combine(start_date, time(23, 59, 59)))

        interest_count = Interest.objects.filter(
            house__user__isnull=False,
            interest=Interest.INTEREST_YES,
            modified__gte=start_date,
            modified__lte=end_date,
            house__user__user_type=ApplicationUser.TYPE_CHOICES.agent,
            house__user=self.request.user,
            house__status=House.HOUSE_STATUSES.published,
        ).count()

        house = (
            House.objects.filter(
                status=House.HOUSE_STATUSES.published, user=self.request.user
            )
            .exclude(main_photo__isnull=True)
            .exclude(main_photo__exact="")
            .last()
        )

        if house:
            response = my_serializers_v3.HouseListSerializer(
                house, context={"request": self.request}
            ).data
            response["day_interested"] = Interest.objects.filter(
                house=house,
                interest=Interest.INTEREST_YES,
                modified__date__gte=(
                    datetime.now() - timedelta(2)
                    if datetime.now().strftime("%A") == "Monday"
                    else datetime.now() - timedelta(1)
                ),
            ).count()
            response["yesterday_interest_count"] = interest_count
        else:
            response = {"yesterday_interest_count": interest_count}
        return Response(response, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["GET"],
        url_name="check_my_appointments",
        url_path="check-my-appointments",
    )
    def check_my_appointments(self, request, *args, **kwargs):
        house = self.get_object()
        now_timerange = (
            timezone.now(),
            timezone.now() + timezone.timedelta(microseconds=1),
        )
        return Response(
            data={
                "has_active_appointments": (
                    AppointmentProposal.objects.filter(
                        sender=request.user,
                        house=house,
                        proposal_state=AppointmentProposal.PROPOSAL_STATES.pending,
                    )
                    .exclude(scheduled_date__fully_lt=now_timerange)
                    .exists()
                    or UserAppointment.objects.filter(
                        sender=request.user,
                        house=house,
                        is_active=True,
                    )
                    .exclude(scheduled_date__fully_lt=now_timerange)
                    .exists()
                ),
            },
        )

    @action(
        detail=True,
        methods=["GET"],
        url_name="generate_pdf",
        url_path="generate-pdf",
        permission_classes=[IsAuthenticated],
    )
    def generate_pdf(self, request, *args, **kwargs):
        """This function is used for generate house pdf and sending to other user with mail.
        if image is not loaded then weasyprint package uninstall and the install again
        """
        house = self.get_object()
        if house.disable_sharing:
            raise NotFound(_("sharing disable"))
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = "attachment; filename=pdf_house.pdf"
        image = house.main_photo_thumbnail if house.main_photo_thumbnail else None
        if image:
            encoded_string = base64.b64encode(image.file.open().read())
            photo_encode = f'data:image/png;base64,{encoded_string.decode("utf-8")}'
        else:
            photo_encode = None

        photos_encode = []
        if house.action == House.ACTION_TYPES.sell:
            house_action = "For Sale"
        else:
            house_action = "Rent"
        for photo in house.photos.all():
            if house.main_photo_thumbnail:
                if not str(photo.image) == house.main_photo.name:
                    encoded_string = base64.b64encode(
                        photo.thumbnail.file.open().read()
                    )
                    photos_encode.append(
                        f'data:image/png;base64,{encoded_string.decode("utf-8")}'
                    )
            else:
                encoded_string = base64.b64encode(photo.thumbnail.file.open().read())
                photos_encode.append(
                    f'data:image/png;base64,{encoded_string.decode("utf-8")}'
                )

        if house.hide_address and house.street_number:
            raw_address = house.raw_address.replace(house.street_number, "", 1)
        else:
            raw_address = house.raw_address
        raw_address = raw_address.split(",")
        raw_address.pop(-1)
        house_raw_address = ",".join(raw_address)

        html = render_to_string(
            "pdf/pdf.html",
            {
                "house": house,
                "house_raw_address": house_raw_address,
                "main_photo_pdf": photo_encode,
                "photos": photos_encode,
                "house_action": house_action,
                "user": self.request.user,
            },
        )

        HTML(string=html).write_pdf(response)
        return response


class AllHousesViewSet(
    HousePublicActionsViewMixin,
    MultiSerializerViewSetMixin,
    SwitchableCursorPaginationViewMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = House.objects.filter(
        status=House.HOUSE_STATUSES.published
    ).select_related("user", "user__agency")
    serializer_action_classes = {
        "list": all_serializers.HouseListSerializer,
    }
    serializer_class = all_serializers.HouseDetailSerializer
    filter_backends = (
        InterestFilterBackend,
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    )
    filterset_class = HousesFilterSet
    search_fields = ["raw_address", "user__full_name"]
    ordering = "-created"

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                Prefetch("photos", HousePhoto.objects.order_by("-is_main", "added_at")),
            )
        return queryset


class AllHousesV2ViewSet(
    HousePublicActionsViewMixin,
    MultiSerializerViewSetMixin,
    SwitchableCursorPaginationViewMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = (
        House.objects.filter(status=House.HOUSE_STATUSES.published)
        .exclude(main_photo__isnull=True)
        .exclude(main_photo__exact="")
        .select_related("user", "user__agency")
    )
    serializer_action_classes = {
        "list": all_serializers_v2.HouseListSerializer,
    }
    serializer_class = all_serializers_v2.HouseDetailSerializer
    filter_backends = (
        InterestFilterBackend,
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    )
    filterset_class = HousesFilterSet
    search_fields = ["raw_address", "user__full_name"]
    ordering = "-created"

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                Prefetch("photos", HousePhoto.objects.order_by("-is_main", "added_at")),
            )
        return queryset


class AllHousesInterestViewSet(
    HousePublicActionsViewMixin,
    MultiSerializerViewSetMixin,
    SwitchableCursorPaginationViewMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = Interest.objects.all()
    serializer_class = all_serializers_v2.AllHouseInterestSerializer
    filter_backends = (
        HouseInterestFilterBackend,
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    )
    search_fields = ["house__raw_address", "house__user__full_name"]
    ordering = "-modified"

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)

            data = json.loads(
                json.dumps(self.get_paginated_response(serializer.data).data)
            )
            temp_data = []
            for obj in data["results"]:
                temp_data.append(obj["house_data"])
            data["results"] = temp_data
            return Response(data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class HousePhotosViewSet(BasePhotosViewSet):
    queryset = HousePhoto.objects.filter(code="photos").order_by("-is_main", "added_at")
    serializer_class = my_serializers.HousePhotoSerializer
    related_model = House


class HouseFloorPlanPhotosViewSet(BasePhotosViewSet):
    queryset = FloorPlan.objects.filter(code="floor_plans")
    serializer_class = my_serializers.FloorPlansSerializer
    related_model = House


class HouseAttachmentViewSet(BasePhotosViewSet):
    queryset = Attachment.objects.all()
    serializer_class = my_serializers.AttachmentSerializer
    related_model = House


class TestPushNotifcation(APIView):
    def get(self, request):
        house_id = request.query_params.get("house_id")
        if not house_id:
            return Response(
                {"message": "house_id should be provided in query params!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user_id := request.query_params.get("user_id"):
            user = get_object_or_404(ApplicationUser, id=user_id)
        else:
            user = request.user

        house = get_object_or_404(House, id=house_id)

        push_notification_types = [x[0] for x in PushNotification.PUSH_TYPES]
        push_type = request.query_params.get(
            "push_type", PushNotification.PUSH_TYPES.my_listing
        )
        if push_type not in push_notification_types:
            return Response(
                {
                    "message": f"Invalid push_type value! push_type can be one of {', '.join(push_notification_types)}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        extra = {}
        # Set the ntification sound to default as per ticket: https://trello.com/c/D2VaMMjW/309-knock-sound-api-update
        # extra.setdefault('sound', PushNotification.SOUNDS_KNOCK_KNOCK)

        # if request.query_params.get('default_sound'):
        #     extra.setdefault('sound', 'default')

        address = PushNotification.hide_address_in_house(house)
        title = f"Testing Push Notification - {datetime.now(timezone.utc)}"

        print(f'Sending "{push_type}" to {user}: "{title}"')

        PushNotification._send_notification(
            user.id,
            _(title),
            address,
            push_type=push_type,
            data={"house_id": house.id},
            **extra,
        )

        return Response(
            {
                "message": f"Successfully sent the notification {push_type} to user {user.id} with the sound {extra.get('sound')}"
            }
        )


class SendHousePropertyToAllViewSet(mixins.UpdateModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated, IsHouseCreator]
    serializer_class = my_serializers_v3.SendToAllSerializer
    queryset = House.objects.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
