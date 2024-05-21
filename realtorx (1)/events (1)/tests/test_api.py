from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from rest_framework import status

from realtorx.custom_auth.tests.factories import UserFactory
from realtorx.events.models import Event
from realtorx.events.tests.factories import EventFactory
from realtorx.utils.tests import APITestCaseMixin


class EventsApiTestCase(APITestCaseMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()

    def setUp(self) -> None:
        super().setUp()

        for event_type in dict(Event.EVENT_TYPES).keys():
            cache.delete(f"event_{self.user.id}_{event_type}")

    def test_get_events_amount(self):
        EventFactory.create_batch(5, user=self.user)

        response = self.forced_auth_req(
            user=self.user, url=reverse("events:events-count"), method="get"
        )

        self.assertEqual(response.data["events_amount"], 5)

    def test_reset_chat_event(self):
        events = EventFactory.create_batch(size=5, kind="unread_thread", user=self.user)
        EventFactory(kind="new_connection", user=self.user)

        response = self.forced_auth_req(
            user=self.user,
            url=reverse("events:events-reset"),
            method="post",
            data={"type": "unread_thread", "chat_id": events[0].chat.chat_id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["events_amount"], 5)
        self.assertEqual(response.data["by_type"]["unread_thread"], 4)

    def test_reset_connection_event(self):
        events = EventFactory.create_batch(
            size=5, kind="new_connection", user=self.user
        )
        EventFactory(kind="unread_thread", user=self.user)

        response = self.forced_auth_req(
            user=self.user,
            url=reverse("events:events-reset"),
            method="post",
            data={
                "type": "new_connection",
                "connection_sender": events[0].initiator.uuid,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["events_amount"], 5)
        self.assertEqual(response.data["by_type"]["new_connection"], 4)
