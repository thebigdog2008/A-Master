import time


from django.core.management.base import BaseCommand


from django.utils.translation import gettext_lazy as _

from realtorx.custom_auth.models import ApplicationUser
from realtorx.houses.models import House
from realtorx.push_notification.handlers import PushNotification


# An exact copy of the real function so we can debug.
# realtorx.push_notification.handlers.push_notification_about_agents_own_listhub_listing
def send_my_listing_push_notification(user, house, **extra):

    # Set the ntification sound to default as per ticket: https://trello.com/c/D2VaMMjW/309-knock-sound-api-update
    # extra.setdefault('sound', PushNotification.SOUNDS_KNOCK_KNOCK)

    address = PushNotification.hide_address_in_house(house)

    now = int(time.time())

    title = f"Test: My Listing - {now}"

    print(f'Sending "my_listing" to {user}: "{title}"')

    PushNotification._send_notification(
        user.id,
        _(title),
        address,
        push_type=PushNotification.PUSH_TYPES.my_listing,
        # push_type=PushNotification.PUSH_TYPES.new_message,
        data={"house_id": house.id},
        **extra,
    )


# realtorx.push_notification.handlers.push_notification_about_new_listing
def send_new_listing_push_notification(user, house, **extra):
    # Set the ntification sound to default as per ticket: https://trello.com/c/D2VaMMjW/309-knock-sound-api-update
    # extra.setdefault('sound', PushNotification.SOUNDS_KNOCK_KNOCK)
    address = PushNotification.hide_address_in_house(house)

    now = int(time.time())

    title = f"Test: New Listing - {now}"

    print(f'Sending "new_listing" to {user}: {title}...')

    from realtorx.push_notification.tasks import send_push_notification_constructed

    if extra.get("sound", None) is None:
        extra.setdefault("sound", "default")

    send_push_notification_constructed.delay(
        user.id,
        _(title),
        address,
        push_type=PushNotification.PUSH_TYPES.new_listing,
        data={"house_id": house.id},
        **extra,
    )


class Command(BaseCommand):

    help = """Test push notifications"""

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="")
        # parser.add_argument('listing_type', type=str, help='"my" or "new"')

    def handle(self, *args, **kwargs):

        # send_push_notification_constructed(1, 'title', 'body', 'push_type')
        # exit()

        user = ApplicationUser.objects.filter(email=kwargs.get("email")).first()

        # Select the latest house in database as a test
        house_filter = {"status": "published", "created_from_listhub": True}
        house = House.objects.order_by("-modified").filter(**house_filter).first()

        # Send both notifications -- see what happens.
        # send_my_listing_push_notification(user, house)
        send_new_listing_push_notification(user, house)

        print(f"Sending push notification to {user} ({user.id}) about {house}")

        # PushNotification._send_notification(
        #     user_id=user.id,
        #     title=title,
        #     body=address,
        #     push_type=push_type,
        #     data={'house_id': house.id},
        #     # sound=PushNotification.SOUNDS_KNOCK_KNOCK,
        #     **extra,
        # )
