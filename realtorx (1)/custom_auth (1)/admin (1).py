from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from realtorx.custom_auth.models import ApplicationUser, BrokerLicence


class ApplicationUserAdmin(UserAdmin):
    list_display = ("username", "email", "full_name", "is_staff", "date_joined")
    search_fields = ("username", "email", "full_name")
    readonly_fields = ("date_joined",)


admin.site.register(ApplicationUser, ApplicationUserAdmin)
admin.site.register(BrokerLicence)
