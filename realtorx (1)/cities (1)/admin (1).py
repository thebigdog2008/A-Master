from django.contrib import admin

from realtorx.cities.models import City


class CitiesAdmin(admin.ModelAdmin):
    list_display = ("state", "county", "name")
    list_filter = ("state",)
    search_fields = ("state", "county", "name")


admin.site.register(City, CitiesAdmin)
