from collections import namedtuple

# Temp commenting code to stop send unread message

# from realtorx.appointments.tasks import notify_user_about_new_appointment_proposal
from realtorx.custom_auth.models import ApplicationUser

# from realtorx.house_chats.tasks import notify_user_about_unread_threads


class UserEmailNotificationEnabledHandler:
    """
    Handler does not send email if user toggle off email_notifications_enabled
    """

    NOTIFICATION_TYPES = namedtuple(
        "NOTIFICATION_TYPES", ["unread_thread", "new_appointment_proposal"]
    )
    NOTIFICATION_TYPES_MAPPING = {
        NOTIFICATION_TYPES.unread_thread: "_unread_thread",
        NOTIFICATION_TYPES.new_appointment_proposal: "_new_appointment_proposal",
    }

    def __init__(self, user: ApplicationUser):
        self.user = user

    def dispatcher(self, notification_type: str, *args, **kwargs):
        """
        :param notification_type: a value for run appropriate celery task
        :param args: is sending to a celery task
        :param kwargs: is sending to a celery task
        """
        if (
            not self.user.email_notifications_enabled
            or self.user.connection_email_unsubscribe
        ):
            return

        f = getattr(self, self.NOTIFICATION_TYPES_MAPPING[notification_type])

        f(*args, **kwargs)

    # Temp commenting code to stop send unread message

    def _unread_thread(self, *args, **kwargs):
        pass

    #     notify_user_about_unread_threads.delay(*args, **kwargs)

    def _new_appointment_proposal(self, *args, **kwargs):
        pass

    #     notify_user_about_new_appointment_proposal.apply_async(*args, **kwargs)
