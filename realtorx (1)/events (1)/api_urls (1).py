from django.urls import include, path

from rest_framework import routers

from . import api

router = routers.SimpleRouter()
router.register("events", api.EventViewSet, basename="events")

app_name = "events"

urlpatterns = [
    path("", include(router.urls)),
]
