from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.utils.translation import gettext as _

from rest_framework.exceptions import PermissionDenied

from realtorx.custom_auth.models import ApplicationUser


class CustomModelBackend(ModelBackend):
    """
    Authenticate user using email or username
    """

    def authenticate(
        self, request, username=None, email=None, phone=None, password=None, **kwargs
    ):
        if not username and not email and not phone:
            return None

        user_model = get_user_model()

        username_query_dict = {"username__iexact": username}
        email_query_dict = {"email__iexact": email}
        phone_query_dict = {"phone": phone.as_international if phone else phone}

        try:
            query_filter = Q()
            if username:
                query_filter |= Q(**username_query_dict)
            if email:
                query_filter |= Q(**email_query_dict)
            if phone:
                query_filter |= Q(**phone_query_dict)

            user = user_model.objects.get(query_filter)

            if not user.is_active:
                raise PermissionDenied(_("User is not active."))

        except user_model.DoesNotExist:
            return None
        else:
            if user.check_password(password):
                if user.send_email_with_temp_password:
                    user.send_email_with_temp_password = False
                    user.save()
                if user.first_login:
                    user.date_first_login = datetime.now()
                    user.first_login = False
                    user.agent_type = ApplicationUser.AGENT_TYPE_CHOICES.agent1
                    user.save(
                        update_fields=["date_first_login", "first_login", "agent_type"]
                    )

                if not user.group_login and not user.is_superuser:
                    group_user = (
                        ApplicationUser.objects.filter(group_login=True)
                        .order_by("-group_login_date")
                        .first()
                    )
                    if group_user:
                        if group_user.group_number < 240:
                            user.group_number = group_user.group_number + 1
                        else:
                            user.group_number = 1
                    else:
                        user.group_number = 1
                    user.group_login_date = datetime.now()
                    user.group_login = True
                    user.save(
                        update_fields=[
                            "group_number",
                            "group_login_date",
                            "group_login",
                        ]
                    )
                user.last_login = datetime.now()
                user.save()
                return user

        return None
