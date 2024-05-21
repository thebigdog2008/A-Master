from django.urls import include, path

from rest_framework.routers import SimpleRouter

from realtorx.registrations.api_web import RegistrationViewSet

router = SimpleRouter()

router.register("", RegistrationViewSet, basename="registration")


app_name = "registration-web"

urlpatterns = [
    path("", include(router.urls)),
]
