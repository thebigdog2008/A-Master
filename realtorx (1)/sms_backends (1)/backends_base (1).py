from django.conf import settings

from twilio.rest import Client


class TwilioClient:
    def __init__(self):
        self.twilio_account_sid = settings.TWILIO_ACCOUNT_SID
        self.twilio_auth_token = settings.TWILIO_AUTH_TOKEN
        self.twilio_phone = settings.TWILIO_PHONE
        self.twilio_verify_service = settings.TWILIO_VERIFY_SERVICE
        self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)

    def create_service(self):
        return NotImplemented

    def send_code_verify(self, to):
        return NotImplemented

    def check_verify(self, to, code):
        return NotImplemented

    def send_message(self, body, to):
        return NotImplemented

    def check_number(self, phone):
        return NotImplemented
