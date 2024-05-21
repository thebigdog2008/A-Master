from django.core.files.base import ContentFile

import requests

from realtorx.photo.serializers import UserPhotoSerializer


def fetch_profile_picture(response=None, user=None, **kwargs):
    if not user:
        return

    if user.avatar:
        return

    received_photo = response.get("picture")

    if not received_photo:
        return

    photo_url = (
        received_photo.get("data")["url"]
        if hasattr(received_photo, "get")
        else received_photo
    )
    photo_content = ContentFile(
        content=requests.get(photo_url).content, name="image.jpg"
    )

    serializer = UserPhotoSerializer(user, data={"image": photo_content})

    if not serializer.is_valid():
        return

    serializer.save()


def user_details_custom(strategy, details, backend, user=None, *args, **kwargs):
    """'user_details' changed for prevent rewriting by empty value

    before: if current_value == value:
    after:  if current_value == value or (type(value) == str and value.strip() == ''):
    """

    """Update user details using data from provider."""
    if not user:
        return

    changed = False  # flag to track changes

    # Default protected user fields (username, id, pk and email) can be ignored
    # by setting the SOCIAL_AUTH_NO_DEFAULT_PROTECTED_USER_FIELDS to True
    if strategy.setting("NO_DEFAULT_PROTECTED_USER_FIELDS") is True:
        protected = ()
    else:
        protected = (
            "username",
            "id",
            "pk",
            "email",
            "password",
            "is_active",
            "is_staff",
            "is_superuser",
        )

    protected = protected + tuple(strategy.setting("PROTECTED_USER_FIELDS", []))

    # Update user model attributes with the new data sent by the current
    # provider. Update on some attributes is disabled by default, for
    # example username and id fields. It's also possible to disable update
    # on fields defined in SOCIAL_AUTH_PROTECTED_USER_FIELDS.
    field_mapping = strategy.setting("USER_FIELD_MAPPING", {}, backend)
    for name, value in details.items():
        # Convert to existing user field if mapping exists
        name = field_mapping.get(name, name)
        if value is None or not hasattr(user, name) or name in protected:
            continue

        current_value = getattr(user, name, None)

        if current_value == value or (type(value) == str and value.strip() == ""):
            continue

        changed = True
        setattr(user, name, value)

    if changed:
        strategy.storage.user.changed(user)
