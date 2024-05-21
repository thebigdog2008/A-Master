# admin.py

from django.contrib import admin
from .models import Agency, AgencyBranch  # Remove TempAgencyBranch import


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ("name", "about", "listhub_validation")
    search_fields = ("name",)


@admin.register(AgencyBranch)
class AgencyBranchAdmin(admin.ModelAdmin):
    list_display = (
        "List_office_name",
        "list_office_address1",
        "list_office_city",
        "list_office_state",
        "list_office_postal_code",
        "agency",
        "list_office_phone",
        "created_from_listhub",
        "sql_validation",
        "sql_state",
    )
    search_fields = (
        "List_office_name",
        "list_office_address1",
        "list_office_city",
        "list_office_postal_code",
    )
    list_filter = ("list_office_state", "agency")


# Remove the registration of TempAgencyBranchAdmin
