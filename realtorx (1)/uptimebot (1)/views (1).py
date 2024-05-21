import json

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from realtorx.uptimebot.tasks import send_pong_to_uptimebot


@require_POST
@csrf_exempt
def ping(request):
    event = json.loads(request.body)
    event_type = event["type"]

    if event_type == "url_verification":
        return HttpResponse(event["challenge"])

    if event["verification_token"] != settings.UPTIMEBOT_TOKEN:
        return HttpResponse(status=401)

    if event_type == "ping":
        send_pong_to_uptimebot.apply_async(
            (event["pong_url"],),
            countdown=event["service_delay"],
        )
    return HttpResponse(status=200)
