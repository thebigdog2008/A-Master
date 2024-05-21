from django.contrib.contenttypes.models import ContentType

from rest_framework import viewsets

from unicef_restlib.views import NestedViewSetMixin

from realtorx.photo.models import Photo
from realtorx.photo.serializers import BasePhotoSerializer


class BasePhotosViewSet(
    NestedViewSetMixin,
    viewsets.ModelViewSet,
):
    queryset = Photo.objects.all()
    serializer_class = BasePhotoSerializer
    related_model = None

    def get_parent_filter(self):
        parent = self.get_parent_object()
        if not parent:
            return {}

        return {
            "content_type_id": ContentType.objects.get_for_model(self.related_model).id,
            "object_id": parent.pk,
        }

    def perform_create(self, serializer):
        return serializer.save(content_object=self.get_parent_object())
