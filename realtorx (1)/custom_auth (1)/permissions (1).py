from rest_framework import permissions


class IsLicenceOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsSelf(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user


class IsSelfOrReadOnly(IsSelf):
    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or super(
            IsSelfOrReadOnly, self
        ).has_object_permission(request, view, obj)


class ObjIsAuthenticated(permissions.BasePermission):
    """
    This permission needed for disable `/users/me/` endpoint for AnonymousUser.
    Unlike IsAuthenticated permission it doesn't disable another functions of viewset.
    """

    def has_object_permission(self, request, view, obj):
        return obj.is_authenticated()


class IsCreateAction(permissions.BasePermission):
    def has_permission(self, request, view):
        return view.action == "create"

    def has_object_permission(self, request, view, obj):
        return False
