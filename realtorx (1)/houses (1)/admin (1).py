# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    House,
    HousePhoto,
    Interest,
    SavedFilter,
    IncomingListing,
    BongoLicence,
    Agent,
)


@admin.register(BongoLicence)
class BongoLicenceAdmin(admin.ModelAdmin):
    pass


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ["email", "full_name", "mls_id", "agency_branch"]
    search_fields = ["email", "full_name", "mls_id"]
    list_filter = ["agency_branch"]


class HousePhotoInline(admin.TabularInline):
    model = HousePhoto
    extra = 1


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ["house_id", "property_type", "city", "state", "price", "agent"]
    search_fields = ["house_id", "city", "state"]
    list_filter = ["property_type", "city", "state", "agent"]
    inlines = [HousePhotoInline]


@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ["user", "house", "interest", "system_generated"]
    search_fields = ["user__username", "house__house_id"]
    list_filter = ["interest", "system_generated"]


@admin.register(SavedFilter)
class SavedFilterAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "action", "city", "state"]
    search_fields = ["name", "user__username"]
    list_filter = ["action", "city", "state"]


@admin.register(IncomingListing)
class IncomingListingAdmin(admin.ModelAdmin):
    list_display = ["id", "created_at", "processed_at"]
    search_fields = ["id"]
    list_filter = ["created_at", "processed_at"]


# Register the UserAdmin with the base class
admin.site.register(User, UserAdmin)

# Register models
admin.site.register(House)
admin.site.register(HousePhoto)
admin.site.register(Interest)
admin.site.register(SavedFilter)
admin.site.register(IncomingListing)
