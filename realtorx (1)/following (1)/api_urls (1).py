from django.urls import include, path

from rest_framework import routers

from realtorx.following import api

router = routers.SimpleRouter()
router.register(r"v1/users", api.FollowingV1ViewSet, basename="users_v1")
router.register(r"v1/groups", api.GroupViewSet, basename="groups_v1")
router.register(r"v1/groups-filter", api.FilterGroupViewSet, basename="groups_v1")
router.register(r"v2/groups", api.GroupV2ViewSet, basename="groups_v2")
router.register(r"v2/users", api.FollowingV2ViewSet, basename="users_v2")
router.register(r"v2/send_to_users", api.FollowingV3ViewSet, basename="users_v2")
router.register(r"v4/users", api.FollowingV4ViewSet, basename="users_v4")
router.register(
    r"v5/send_to_interested_users", api.FollowingV5ViewSet, basename="users_v5"
),

router.register(r"v1/my-connection", api.MyConnectionV1ViewSet, basename="testing"),
router.register(r"v1/database", api.DatabaseV1ViewSet, basename="testing_for_database")


app_name = "following"

urlpatterns = [
    path("", include(router.urls)),
    path(
        r"accept/<str:uuid>", api.AcceptRenderTemplate.as_view(), name="accept_template"
    ),
    path(
        r"unsubscribe/<str:uuid>",
        api.UnsubscribeEmail.as_view(),
        name="unsubscribe_connection",
    ),
    path(r"remove-groups/", api.remove_group, name="remove-groups"),
    path(r"connect/", api.create_following_requests_from_number, name="connect"),
]
