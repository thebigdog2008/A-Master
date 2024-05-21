from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from realtorx.custom_auth.models import ApplicationUser, BrokerLicence
from realtorx.custom_auth.serializers import (
    ApplicationUserSerializer,
    BrokerLicenceSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = ApplicationUser.objects.all()
    serializer_class = ApplicationUserSerializer


class BrokerLicenceView(viewsets.ModelViewSet):
    queryset = BrokerLicence.objects.all()
    serializer_class = BrokerLicenceSerializer


class UserAuthViewSet(viewsets.ViewSet):
    def create(self, request):
        # Your authentication logic here
        return Response({"message": "Authentication logic goes here"})


class UserViewSetV2(viewsets.ModelViewSet):
    queryset = ApplicationUser.objects.all()
    serializer_class = ApplicationUserSerializer


class UserViewSetV3(viewsets.ModelViewSet):
    queryset = ApplicationUser.objects.all()
    serializer_class = ApplicationUserSerializer


class emailVerify(APIView):
    def get(self, request, uuid):
        # Your email verification logic here
        return Response({"message": "Email verification logic goes here"})


def save_filter(request):
    # Your save filter logic here
    pass


def demo(request):
    # Your demo logic here
    pass


def testing_listhub(request):
    # Your testing listhub logic here
    pass
