from django.urls import re_path

from realtorx.ui.views import store_redirect

app_name = "ui"

urlpatterns = [
    re_path(r"^store-redirect/(?P<name>\w+)", store_redirect, name="store_redirect"),
]
