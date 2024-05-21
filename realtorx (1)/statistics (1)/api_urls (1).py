from django.urls import include, path

from rest_framework import routers

from realtorx.statistics.api import StatisticViewSet, StatisticViewSetV2
from realtorx.statistics.api_web import StatisticWebViewSet, StatisticWebViewSetV2
from realtorx.statistics.views import daily_statistics, statistic_count

router = routers.SimpleRouter()

router.register("statistics", StatisticViewSet, basename="statistics")
router.register("v2/statistics", StatisticViewSetV2, basename="statistics_v2")

web_router = routers.SimpleRouter()

web_router.register("statistics", StatisticWebViewSet, basename="statistics_web")
web_router.register(
    "v2/statistics", StatisticWebViewSetV2, basename="statistics_web_v2"
)


app_name = "statistics"

urlpatterns = [
    path("", include(router.urls)),
    path("web/", include(web_router.urls)),
    path("daily-statistics/", daily_statistics, name="daily_statistics"),
    path("statistic-count/", statistic_count, name="statistic_count"),
]
