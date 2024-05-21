from django.contrib.auth.forms import UserCreationForm

from realtorx.custom_auth.models import ApplicationUser


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = ApplicationUser
        fields = UserCreationForm.Meta.fields + ("full_name", "email")
