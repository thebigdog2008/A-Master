from import_export import resources
from .models import *


class ApplicationUserResource(resources.ModelResource):
    class Meta:
        model = ApplicationUser
        fields = (
            "email",
            "phone",
            "username",
            "full_name",
            "date_first_login",
            "last_login",
        )
