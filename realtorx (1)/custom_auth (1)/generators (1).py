from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import six


class EmailConfirmTokenGenerator(PasswordResetTokenGenerator):
    key_salt = "realtorx.custom_auth.generators.EmailConfirmTokenGenerator"

    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk)
            + user.email
            + six.text_type(user.is_active)
            + six.text_type(timestamp)
        )
