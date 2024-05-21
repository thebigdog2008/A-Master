from realtorx.properties.models import RateLimit


def get_rate_limit_value(group, request):
    rate_limit = RateLimit.objects.filter(key="rate-limit").values("value")
    if rate_limit:
        return rate_limit[0].get("value")
    else:
        return "5/m"
