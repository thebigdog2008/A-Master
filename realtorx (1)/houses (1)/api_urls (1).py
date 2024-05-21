from django.urls import include, path

from rest_framework import routers

from unicef_restlib.routers import NestedComplexRouter

from realtorx.houses.api import house_web
from realtorx.houses.api.house import (
    AllHousesV2ViewSet,
    AllHousesViewSet,
    HouseAttachmentViewSet,
    HouseFloorPlanPhotosViewSet,
    HousePhotosViewSet,
    MyHousesV3ViewSet,
    MyHousesV2ViewSet,
    MyHousesViewSet,
    SearchHousesV2ViewSet,
    SearchHousesViewSet,
    AllHousesInterestViewSet,
    TestPushNotifcation,
    SendHousePropertyToAllViewSet,
)
from realtorx.houses.api.saved_filters import (
    SavedFiltersV2ViewSet,
    SavedFiltersViewSet,
    MySearchHousesViewSet,
    JustBrowsingHousesViewSet,
)

api_router = routers.SimpleRouter()
api_router.register(
    r"v1/houses/search", SearchHousesViewSet, basename="houses_search_v1"
)
api_router.register(
    r"v2/houses/search", SearchHousesV2ViewSet, basename="houses_search_v2"
)
api_router.register(r"v1/houses/my", MyHousesViewSet, basename="houses_my_v1")
api_router.register(r"v2/houses/my", MyHousesV2ViewSet, basename="houses_my_v2")
api_router.register(r"v3/houses/my", MyHousesV3ViewSet, basename="houses_my_v3")
api_router.register(r"v1/houses/all", AllHousesViewSet, basename="houses_all_v1")
api_router.register(r"v2/houses/all", AllHousesV2ViewSet, basename="houses_all_v2")
api_router.register(
    r"v1/houses/interest", AllHousesInterestViewSet, basename="houses_all_interest"
)
api_router.register(
    r"v1/saved-filters", SavedFiltersViewSet, basename="saved_filters_v1"
)
api_router.register(
    r"v2/saved-filters", SavedFiltersV2ViewSet, basename="saved_filters_v2"
)
api_router.register(
    r"v1/my/houses/search", MySearchHousesViewSet, basename="houses_my_search_v1"
)  # used for search screen
api_router.register(
    r"v3/houses/send-to-all",
    SendHousePropertyToAllViewSet,
    basename="houses_send_to_all",
)


# API For Guest Login Users
api_router.register(
    r"v1/just_browsing", JustBrowsingHousesViewSet, basename="houses_just_browsing"
)

houses_router = NestedComplexRouter(api_router, r"v1/houses/my")
houses_router.register(r"photos", HousePhotosViewSet, basename="house-photos")
houses_router.register(
    r"floor-plan-photos",
    HouseFloorPlanPhotosViewSet,
    basename="house-floor_plan_photos",
)
houses_router.register(
    r"attachments", HouseAttachmentViewSet, basename="house-attachments"
)

web_router = routers.SimpleRouter()
web_router.register(
    r"web/houses/my", house_web.MyHousesViewSet, basename="houses_my_web"
)

web_houses_router = NestedComplexRouter(web_router, r"web/houses/my", lookup="house")
web_houses_router.register(
    r"interests", house_web.MyHouseInterestsViewSet, basename="house_my_interests_web"
)

app_name = "houses"

urlpatterns = [
    path("", include(houses_router.urls)),
    path("", include(api_router.urls)),
    path("", include(web_houses_router.urls)),
    path("", include(web_router.urls)),
    path(
        "test_notifications", TestPushNotifcation.as_view(), name="test_notifications"
    ),
]
