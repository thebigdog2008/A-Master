from mixpanel import Mixpanel
from django.conf import settings
import logging

logger = logging.getLogger("django")

MIXPANEL_EVENT_MESSAGES = {
    "agent_created": "New Agent Created",
    "agent_deleted": "Agent Deleted",
    "agent_type_changed": "Agent Type Changed",
    "filter_added": "New filter added",
    "profile_pic_added": "Profile photo added",
    "new_connection_request_receiver": "Received a new connection",
    "new_connection_request_sender": "Sent a new connection",
    "connection_request_accept": "Connection Accepted",
    "email_sent": "Sent an email to user",
    "send_to_more": "Property has been sent to more users",
    "amazing_property_added": "Property has been added as an Amazing Property",
    "sneak_peak_added": "Property has been added as a Sneak Peak",
    "amazing_property_converted": "Property type has been changed from an Amazing Property into a Sneak Peak",
    "showing_request": "User has requested for showing a property",
    "property_interest": "User has shown interest in a property",
    "email_unsubscribe": "User has requested to opt out for email subscription",
    "duplicate_email_unsubscribe": "Already email unsubscribed",
    "property_not_interested": "User not interested in a property",
    "listhub_metrics": "ListHub Metrics",
    "sendgrid_events": "Sendgrid events",
    "payment_verified": "Payment verified",
    "new_listing_notification": "New Listing Push Notification",
    "new_self_listing_notification": "New Own Listing Push Notification to Agent1",
    "daily_interest_agent_notification": "Daily interest agent push notification",
    "track_whitelist_user_event": "Whitelist User Event",
    "agent3_email_verification_skip": "Agent3 Email Verification Skipped",
    "connection_push_notification_track": "New connection push notification cron job",
}

REVERSE_MIXPANEL_EVENT_MESSAGES = {v: k for k, v in MIXPANEL_EVENT_MESSAGES.items()}


def track_mixpanel_event(user_id: str, event_key: str, data: dict = None) -> None:
    if not settings.MIXPANEL_TRACKING_ENABLED:
        logger.info("Skipping Mixpanel Tracking...")
        return
    mp = Mixpanel(settings.MIXPANEL_TOKEN)
    try:
        mixpanel_data = data if data is not None else {}
        mixpanel_data["environment"] = settings.APP_ENVIRONMENT
        mp.track(user_id, MIXPANEL_EVENT_MESSAGES[event_key], mixpanel_data)
    except Exception as e:
        logger.error(f"Could not send mixpanel event due to => {e}")
