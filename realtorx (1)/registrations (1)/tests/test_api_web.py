from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from django.test import TestCase

from rest_framework import status

from realtorx.custom_auth.tests.factories import UserFactory
from realtorx.utils.tests import TestAPIViewSetMixin

User = get_user_model()


class RegistrationApiTestCase(TestAPIViewSetMixin, TestCase):
    DEFAULT_PHONE_NUMBER = "+375295555555"

    base_view = "registration-web:registration"

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_signup(self):
        response = self.forced_auth_req(
            method="post",
            url=reverse(self.base_view + "-list"),
            data={
                "password": "TesTPa$$w0rd",
                "email": "test@test.com",
                "last_name": "test_last_name",
                "first_name": "test_first_name",
                "state": "WA",
                "phone": self.DEFAULT_PHONE_NUMBER,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_users_by_phone(self):
        user = UserFactory(phone=self.DEFAULT_PHONE_NUMBER)

        response = self.forced_auth_req(
            method="get",
            url=reverse(self.base_view + "-list"),
            data={"phone__in": [self.DEFAULT_PHONE_NUMBER]},
            user=self.user,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["uuid"], str(user.uuid))

    @patch(
        "realtorx.registrations.auth_backends.apple.AppleIdAuth.get_user_details",
        return_value=({"email": "test@example.com"}),
    )
    @patch(
        "realtorx.registrations.auth_backends.apple.AppleIdAuth.decode_id_token",
        return_value={},
    )
    @patch(
        "realtorx.registrations.auth_backends.apple.AppleIdAuth.exchange_access_token",
        return_value={"id_token": "id_token"},
    )
    def test_apple_id_oauth(self, _1, _2, _3):
        response = self.forced_auth_req(
            "post",
            reverse(f"{self.base_view}-social-auth", args=("apple-id",)),
            data={
                "access_token": "test",
                "user_extra_data": {"first_name": "Test", "last_name": "User"},
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["first_name"], "Test")
        self.assertEqual(response.data["last_name"], "User")
        self.assertEqual(response.data["full_name"], "Test User")

    @patch(
        "realtorx.registrations.auth_backends.apple.AppleIdAuth.get_user_details",
        return_value=({"email": "test@example.com"}),
    )
    @patch(
        "realtorx.registrations.auth_backends.apple.AppleIdAuth.decode_id_token",
        return_value={},
    )
    @patch(
        "realtorx.registrations.auth_backends.apple.AppleIdAuth.exchange_access_token",
        return_value={"id_token": "id_token"},
    )
    def test_prevent_rewriting_social_data_by_empty_value(self, _1, _2, _3):
        responses = [
            self.forced_auth_req(
                "post",
                reverse(f"{self.base_view}-social-auth", args=("apple-id",)),
                data={"access_token": "test", "user_extra_data": user_extra_data},
            )
            for user_extra_data in [
                {"first_name": "Test", "last_name": "User"},
                {"first_name": "", "last_name": ""},
            ]
        ]

        for response in responses:
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data["first_name"], "Test")
            self.assertEqual(response.data["last_name"], "User")
            self.assertEqual(response.data["full_name"], "Test User")
