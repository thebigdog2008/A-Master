from django.contrib import admin

from realtorx.properties.models import KeyValue, RateLimit


class RateLimitAdmin(admin.ModelAdmin):
    list_display = ("key", "value")
    list_filter = ("key", "value")
    search_fields = ("key", "value")

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(RateLimitAdmin, self).get_readonly_fields(request, obj)
        if obj:
            return readonly_fields + ("key",)
        return readonly_fields


class KeyValueAdmin(admin.ModelAdmin):
    list_display = ("key", "value")
    list_filter = ("key", "value")
    search_fields = ("key", "value")

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(KeyValueAdmin, self).get_readonly_fields(request, obj)
        if obj:
            return readonly_fields + ("key",)
        return readonly_fields


admin.site.register(RateLimit, RateLimitAdmin)
admin.site.register(KeyValue, KeyValueAdmin)
