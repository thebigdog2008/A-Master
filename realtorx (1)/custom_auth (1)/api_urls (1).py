from django.urls import include, path
from rest_framework import routers
from realtorx.custom_auth import api, views

router = routers.SimpleRouter()
router.register("v1/licence", api.BrokerLicenceView, basename="licence_v1")
router.register("v1/users", api.UserViewSet, basename="users_v1")
router.register("v1/auth", api.UserAuthViewSet, basename="auth_v1")
router.register("v2/users", api.UserViewSetV2, basename="users_v2")
router.register("v3/users", api.UserViewSetV3, basename="users_v3")

app_name = "custom_auth"
urlpatterns = [
    path("", include(router.urls)),
    path("user-report/", views.userReportAdmin),
    path("email-verify/<str:uuid>/", api.emailVerify.as_view(), name="email_verify"),
    path("save_filter/", api.save_filter, name="save-filter"),
]
