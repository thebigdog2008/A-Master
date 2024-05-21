import json

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from realtorx.utils.mixpanel import track_mixpanel_event


class SendGridWebhookEvent(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        if request.body:
            events = json.loads(request.body)
            for event in events:
                track_mixpanel_event(event["sg_event_id"], "sendgrid_events", event)
        return Response()
