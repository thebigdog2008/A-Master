from rest_framework.permissions import BasePermission


class IsHouseCreator(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsNotHouseCreator(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user != request.user
