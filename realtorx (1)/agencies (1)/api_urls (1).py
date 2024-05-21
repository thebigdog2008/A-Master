from django.urls import include, path

from rest_framework import routers

from realtorx.agencies import api

router = routers.SimpleRouter()
router.register("", api.AgenciesViewSet, basename="agencies")


app_name = "agencies"
urlpatterns = [
    path("", include(router.urls)),
]
