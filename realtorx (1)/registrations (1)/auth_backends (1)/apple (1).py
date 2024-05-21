import json
import time

import jwt
from jwt.algorithms import RSAAlgorithm
from jwt.exceptions import PyJWTError
from social_core.backends.apple import BaseOAuth2
from social_core.exceptions import AuthCanceled

from realtorx.registrations.auth_backends.base import AuthBackendWithExtraData


class AppleIdAuth(BaseOAuth2):
    name = "apple-id"

    JWK_URL = "https://appleid.apple.com/auth/keys"
    AUTHORIZATION_URL = "https://appleid.apple.com/auth/authorize"
    ACCESS_TOKEN_URL = "https://appleid.apple.com/auth/token"
    ACCESS_TOKEN_METHOD = "POST"
    RESPONSE_MODE = None
    ID_KEY = "sub"
    TOKEN_KEY = "id_token"
    STATE_PARAMETER = True
    REDIRECT_STATE = False
    TOKEN_AUDIENCE = "https://appleid.apple.com"
    TOKEN_TTL_SEC = 6 * 30 * 24 * 60 * 60

    def get_private_key(self):
        return self.setting("SECRET")

    def get_client_id(self):
        return self.setting("CLIENT")

    def generate_client_secret(self):
        now = int(time.time())
        client_id = self.get_client_id()
        team_id = self.setting("TEAM")
        key_id = self.setting("KEY")
        private_key = self.get_private_key()
        headers = {"kid": key_id}
        payload = {
            "iss": team_id,
            "iat": now,
            "exp": now + self.TOKEN_TTL_SEC,
            "aud": self.TOKEN_AUDIENCE,
            "sub": client_id,
        }
        return jwt.encode(payload, key=private_key, algorithm="ES256", headers=headers)

    def get_key_and_secret(self):
        client_id = self.get_client_id()
        client_secret = self.generate_client_secret()
        return client_id, client_secret

    def get_apple_jwk(self):
        keys = self.get_json(url=self.JWK_URL).get("keys")
        if not isinstance(keys, list) or not keys:
            raise AuthCanceled("Invalid jwk response")
        return json.dumps(keys.pop())

    def decode_id_token(self, id_token):
        """Decode and validate JWT token from apple and return payload including user data."""
        if not id_token:
            raise AuthCanceled("Missing id_token parameter")

        public_key = RSAAlgorithm.from_jwk(self.get_apple_jwk())

        try:
            decoded = jwt.decode(
                id_token,
                key=public_key,
                audience=self.get_client_id(),
                algorithm="RS256",
                options={"verify_signature": False},
            )
        except PyJWTError:
            raise AuthCanceled("Token validation failed")

        return decoded

    def get_user_details(self, response):
        name = response.get("name") or {}
        fullname, first_name, last_name = self.get_user_names(
            fullname="",
            first_name=name.get("firstName", ""),
            last_name=name.get("lastName", ""),
        )
        email = response.get("email", "")
        apple_id = response.get(self.ID_KEY, "")
        user_details = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
        }

        if email and self.setting("EMAIL_AS_USERNAME"):
            user_details["username"] = email

        if apple_id and not self.setting("EMAIL_AS_USERNAME"):
            user_details["username"] = apple_id
        return user_details

    def exchange_access_token(self, access_token):
        key, secret = self.get_key_and_secret()
        response = self.get_json(
            self.access_token_url(),
            method="POST",
            data={
                "code": access_token,
                "client_id": key,
                "client_secret": secret,
                "grant_type": "authorization_code",
            },
        )
        return response

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        data = self.exchange_access_token(access_token)
        decoded_data = self.decode_id_token(data[self.TOKEN_KEY])
        user_details = self.get_user_details(decoded_data)
        return user_details

    def do_auth(self, access_token, *args, **kwargs):
        data = self.user_data(access_token)
        data["access_token"] = access_token
        kwargs.update({"backend": self, "response": data})
        return self.strategy.authenticate(*args, **kwargs)


class SwitchableAppleIdAuthBackend(AuthBackendWithExtraData, AppleIdAuth):
    def get_client_id(self):
        if hasattr(self, "client_id"):
            return self.client_id
        return super().get_client_id()
