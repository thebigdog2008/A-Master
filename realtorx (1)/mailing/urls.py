from django.urls import path

from realtorx.mailing.views import SendGridWebhookEvent

urlpatterns = [
    path("sendgrid-webhook/", SendGridWebhookEvent.as_view(), name="sendgrid-webhook"),
]
