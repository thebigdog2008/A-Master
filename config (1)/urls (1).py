"""realtorx URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/

Examples:

Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  path('blog/', include(blog_urls))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from django.urls import re_path
from django.contrib.staticfiles.views import serve as serve_static
from rest_framework import permissions
from drf_yasg2.views import get_schema_view
from drf_yasg2 import openapi


def _static_butler(request, path, **kwargs):
    """
    Serve static files using the django static files configuration
    WITHOUT collectstatic. This is slower, but very useful for API
    only servers where the static files are really just for /admin

    Passing insecure=True allows serve_static to process, and ignores
    the DEBUG=False setting
    """
    return serve_static(request, path, insecure=True, **kwargs)


urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api/",
        include(
            [
                path("custom-auth/", include("realtorx.custom_auth.api_urls")),
                path("houses/", include("realtorx.houses.api_urls")),
                path("following/", include("realtorx.following.api_urls")),
                path("statistics/", include("realtorx.statistics.api_urls")),
                path("events/", include("realtorx.events.api_urls")),
                path(
                    "registration/",
                    include(
                        [
                            path("", include("realtorx.registrations.api_urls")),
                            path(
                                "web/", include("realtorx.registrations.api_urls_web")
                            ),
                        ]
                    ),
                ),
                path("cities/", include("realtorx.cities.api_urls")),
                path("agencies/", include("realtorx.agencies.api_urls")),
                path("mail/", include("realtorx.mailing.urls")),
            ]
        ),
    ),
    path("uptime-bot/", include("realtorx.uptimebot.urls")),
    path("ui/", include("realtorx.ui.urls")),
    re_path(r"static/(.+)", _static_butler),
]


schema_view = get_schema_view(
    openapi.Info(
        title="AgentLoop API",
        default_version="v1",
        description="AgentLoop description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=False,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns += [
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
