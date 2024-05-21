from realtorx.sms_backends.backends_base import TwilioClient


class VerifyBackend(TwilioClient):
    def send_code_verify(self, to):
        self.twilio_client.verify.services(
            self.twilio_verify_service
        ).verifications.create(to=to, channel="sms")

    def check_verify(self, to, code):
        return self.twilio_client.verify.services(
            self.twilio_verify_service
        ).verification_checks.create(to=to, code=code)


class SMSBackend(TwilioClient):
    def send_message(self, body, to):
        self.twilio_client.messages.create(body=body, to=to, from_=self.twilio_phone)
