from django.contrib import admin

from realtorx.following.models import ConnectionsGroup, FollowingRequest


class FollowingRequestAdmin(admin.ModelAdmin):
    list_display = ("sender", "recipient", "status")
    list_select_related = ("sender", "recipient")
    list_filter = ("status",)
    search_fields = ("sender__uuid", "recipient__uuid")
    autocomplete_fields = ("sender", "recipient")


class ConnectionsGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "owner")
    list_select_related = ("owner",)
    search_fields = ("owner__uuid", "members__uuid")
    autocomplete_fields = ("owner", "members")


admin.site.register(ConnectionsGroup, ConnectionsGroupAdmin)
admin.site.register(FollowingRequest, FollowingRequestAdmin)
