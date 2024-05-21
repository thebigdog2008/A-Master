from django.core.management.base import BaseCommand

from realtorx.custom_auth.models import ApplicationUser
from realtorx.houses.models import House
from realtorx.mailing.utils import send_templated_mail
from django.urls import reverse
from django.contrib.sites.models import Site
from realtorx.utils.urls import construct_login_url


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "email", type=str, nargs="?", default="agentloop_test@yahoo.com"
        )

    def handle(self, *args, **options):

        # Send it without Celery
        # settings.TEMPLATED_EMAIL_BACKEND = 'templated_email.backends.vanilla_django'

        user = ApplicationUser.objects.filter(email=options.get("email")).first()
        house_filter = {"status": "published", "created_from_listhub": True}
        house = House.objects.order_by("-modified").filter(**house_filter).first()

        street = str(house.street)
        if street.startswith(house.street_number):
            street = street.replace(house.street_number, "")
        street_address = str(house.street_number) + " " + str(street.lstrip())

        domain = Site.objects.get_current().domain
        unsubscribe_url = domain + reverse(
            "following:unsubscribe_connection", kwargs={"uuid": user.uuid}
        )
        login_redirect_url = construct_login_url(user.first_name)

        # print("unsubscribe_url => ", unsubscribe_url)
        # print("login_redirect_url => ", login_redirect_url)

        context = {
            "first_name": user.first_name,
            "address": house.raw_address,
            "city": house.city,
            "phone": str(user.phone),
            "password": "131diELca5",
            "receiver_profile": user.avatar.url if user.avatar else "",
            "house_image": house.main_photo_email_url,
            "unsubscribe_url": unsubscribe_url,
            "login_redirect_url": login_redirect_url,
            "subject_name": f"Missing profile photo for {street_address}",
            "email_type": "page9",
        }

        send_templated_mail(
            user=user,
            template_name="page9_listhub_property_of_A2_whose_profile_is_missing.html",
            from_email="AgentLoop<invitations@agentloop.us>",
            recipient_list=[user.email],
            context=context,
            fail_silently=False,
        )
