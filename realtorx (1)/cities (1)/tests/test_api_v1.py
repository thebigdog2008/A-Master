from django.contrib.auth import get_user_model
from django.test import TestCase

from realtorx.cities.tests.factories import CityFactory
from realtorx.custom_auth.tests.factories import UserFactory
from realtorx.utils.tests import TestAPIViewSetMixin

User = get_user_model()


class TestCitiesViewSet(TestAPIViewSetMixin, TestCase):
    base_view = "cities:cities"

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.city = CityFactory()

    def test_list_cities(self):
        self.make_list_request(self.user)
