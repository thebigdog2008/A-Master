from django.core.cache import cache
from django.test import TestCase

from realtorx.custom_auth.tests.factories import UserFactory
from realtorx.events.models import Event
from realtorx.following.tests.factories import FollowingRequestFactory
from realtorx.utils.tests import APITestCaseMixin


class SpawnEventsApiTestCase(APITestCaseMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.follower = UserFactory()
        cls.user.following.add(cls.follower)

    def setUp(self) -> None:
        super().setUp()

        for event_type in dict(Event.EVENT_TYPES).keys():
            cache.delete(f"event_{self.user.id}_{event_type}")

    def test_increment_on_new_connection(self):
        FollowingRequestFactory.create_batch(size=2, recipient=self.user)
        FollowingRequestFactory(sender=self.user)
        self.assertEqual(Event.get_cached_unseen_events_count(self.user.id), 2)
