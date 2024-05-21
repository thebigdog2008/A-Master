from unittest.mock import patch

from django.test import TestCase

from realtorx.custom_auth.tests.factories import UserFactory
from realtorx.mailing.handlers import UserEmailNotificationEnabledHandler


class UserEmailNotificationEnabledHandlerTestCase(TestCase):
    @patch(
        "realtorx.mailing.handlers.UserEmailNotificationEnabledHandler._unread_thread"
    )
    def test_email_notification_disabled(self, mocked_f):
        user = UserFactory(email_notifications_enabled=False)
        handler = UserEmailNotificationEnabledHandler(user=user)
        handler.dispatcher(
            UserEmailNotificationEnabledHandler.NOTIFICATION_TYPES.unread_thread
        )
        mocked_f.assert_not_called()

    @patch(
        "realtorx.mailing.handlers.UserEmailNotificationEnabledHandler._unread_thread"
    )
    def test_email_notification_enabled(self, mocked_f):
        user = UserFactory()
        handler = UserEmailNotificationEnabledHandler(user=user)
        handler.dispatcher(
            UserEmailNotificationEnabledHandler.NOTIFICATION_TYPES.unread_thread
        )
        mocked_f.assert_called()
