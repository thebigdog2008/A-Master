from django.urls import include, path

from rest_framework.routers import SimpleRouter

from realtorx.registrations.api import (
    RegistrationV2ViewSet,
    RegistrationViewSet,
    RegistrationV3ViewSet,
    RegistrationV4ViewSet,
    TrialUserViewSet,
)

router = SimpleRouter()

router.register("", RegistrationViewSet, basename="registration")
router.register("v2", RegistrationV2ViewSet, basename="registration_v2")
router.register("v3", RegistrationV3ViewSet, basename="registration_v3")
router.register("v4", RegistrationV4ViewSet, basename="registration_v4")
router.register("trialuser", TrialUserViewSet, basename="trialuser")

app_name = "registration"

urlpatterns = [
    path("", include(router.urls)),
]
