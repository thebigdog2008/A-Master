from django.conf import settings
from realtorx.utils.mixpanel import track_mixpanel_event
import json


def send_templated_mail(
    user,
    template_name,
    from_email,
    recipient_list,
    context,
    cc=None,
    bcc=None,
    fail_silently=False,
    connection=None,
    headers=None,
    template_prefix=None,
    template_suffix=None,
    create_link=False,
    **kwargs,
):
    """
    Global function for sending emails

    A very simple wrapper around this package:

        https://pypi.org/project/django-templated-email/

    Emails are sent with Celery, and errors are logged to:

        /data/realtorx-logs/celeryd-realtorx-notifications.log
    """

    if user.connection_email_unsubscribe:
        print(f"User {user} (id={user.id}) has unsubscribed from emails")
        return

    if not settings.EMAILS_ENABLED:

        # If emails are disabled, we send only to email addresses on the allowed list

        # We do this because all emails are currently being sent to a single user
        recipient_email = recipient_list[0]
        if recipient_email not in settings.EMAIL_ALLOWED_ADDRESSES:
            print(
                f"Emails are turned off and <{recipient_email}> is not on the allowed list"
            )
            return

        # If we had multiple recipients we might do this:
        # recipient_list = [r for r in recipient_list if r in settings.EMAIL_ALLOWED_ADDRESSES]
        # if not recipient_list:
        #     print(f'Email not sent')
        #     return

    # Otherwise we can send the email
    from templated_email import send_templated_mail as _send_templated_mail

    print(f"Sending email to {user} (id={user.id})", kwargs)
    mixpanel_data = {
        "email": recipient_list[0] if recipient_list else user.email,
        "phone": str(user.phone),
        "full_name": user.full_name,
        "email_type": context.get("email_type", ""),
        "template_name": template_name,
        "email_unsubscribed": user.connection_email_unsubscribe,
    }
    if "system_generated" in kwargs and kwargs["system_generated"]:
        mixpanel_data["system_generated"] = kwargs["system_generated"]
        mixpanel_data["sender_email"] = kwargs["sender"].email
    if "sender" in kwargs:
        del kwargs["sender"]
    if "system_generated" in kwargs:
        del kwargs["system_generated"]

    track_mixpanel_event(str(user.uuid), "email_sent", mixpanel_data)

    if context.get("email_type", ""):
        headers = {
            "X-SMTPAPI": json.dumps(
                {"unique_args": {"email_type": context["email_type"]}}
            )
        }
    _send_templated_mail(
        template_name=template_name,
        from_email=from_email,
        recipient_list=recipient_list,
        context=context,
        cc=cc,
        bcc=settings.EMAIL_BCC,
        fail_silently=fail_silently,
        connection=connection,
        headers=headers,
        template_prefix=template_prefix,
        template_suffix=template_suffix,
        create_link=None,
        **kwargs,
    )
