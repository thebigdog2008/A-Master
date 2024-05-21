from django.urls import include, path

from rest_framework import routers

from realtorx.cities import api

router = routers.SimpleRouter()
router.register("", api.CitiesViewSet, basename="cities")


app_name = "cities"
urlpatterns = [
    path("", include(router.urls)),
]
