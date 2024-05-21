from django.urls import path

from realtorx.uptimebot.views import ping

urlpatterns = [
    path("ping/", ping),
]
