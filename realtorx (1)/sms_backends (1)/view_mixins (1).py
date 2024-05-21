from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from realtorx.sms_backends.backends import VerifyBackend
from realtorx.sms_backends.serializers import SMSVerificationSerializer


class SMSVerificationCodeSendCheckViewMixin:
    sms_backend_obj = VerifyBackend()

    @action(
        methods=["post"],
        detail=False,
        url_path="check-sms-code",
        url_name="check_sms_code",
        permission_classes=(AllowAny,),
    )
    def check_sms_code(self, *args, **kwargs):
        """
        request.data should contain 'to' - phone number of a user and 'code' - sms code sent to a user
        """
        serializer = self.get_serializer(data=self.request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        return Response()

    def get_serializer_class(self):
        if self.action == "check_sms_code":
            return SMSVerificationSerializer
        return super().get_serializer_class()

    def send_sms_code(self, to: str):
        self.sms_backend_obj.send_code_verify(to)
