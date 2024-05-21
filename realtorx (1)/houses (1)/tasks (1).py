import logging
import pytz
from datetime import datetime, timedelta, time, timezone
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import Q
from django.conf import settings
from django.urls import reverse
from realtorx.custom_auth.models import ApplicationUser
from realtorx.houses.image_processor.image_processor import ImageProcessor
from realtorx.houses.models import House, Interest
from realtorx.mailing.utils import send_templated_mail
from realtorx.taskapp import app
from realtorx.utils.urls import construct_login_url


@app.task
def daily_interest_agent_notification():
    """
    send push notification to agent for getting count for how many users can interested property
    """
    if datetime.now().strftime("%A") == "Monday":
        start_date = pytz.utc.localize(
            datetime.combine((datetime.now().date() - timedelta(2)), time())
        )
        end_date = pytz.utc.localize(
            datetime.combine((start_date.date() + timedelta(1)), time(23, 59, 59))
        )
    else:
        start_date = pytz.utc.localize(
            datetime.combine((datetime.now().date() - timedelta(1)), time())
        )
        end_date = pytz.utc.localize(datetime.combine(start_date, time(23, 59, 59)))

    interest_list = (
        Interest.objects.filter(
            house__user__isnull=False,
            interest=Interest.INTEREST_YES,
            modified__gte=start_date,
            modified__lte=end_date,
            house__user__user_type=ApplicationUser.TYPE_CHOICES.agent,
            house__status=House.HOUSE_STATUSES.published,
        )
        .values("house__user")
        .annotate(total_interest=models.Count("id"))
        .filter(total_interest__gt=0)
        .order_by("house__user")
    )


@app.task
def daily_check_amazing_listing():
    """
    daily check and delete amazing listing for checking there active time according.
    """
    if settings.DAILY_CHECK_OR_DELETE_AMAZING_LISTING:
        houses = House.objects.filter(
            listing_type=House.LISTING_TYPES.amazinglisting, delete_amazing_ack=True
        )
        for house in houses:
            end_date = house.created + timedelta(settings.NUMBER_OF_DAYS)
            if pytz.utc.localize(datetime.now()) > end_date:
                house.delete()


@app.task(soft_time_limit=86400, time_limit=90000)
def fix_house_main_photo():
    logger = logging.getLogger("django")
    logger.info("Starting the FIX for main_photo of listhub listing houses.")
    listhub_houses_start_date = datetime.now(timezone.utc) - timedelta(
        days=120
    )  # approx 4 months
    listhub_houses = House.objects.filter(
        listing_type=House.LISTING_TYPES.listhublisting,
        modified__gte=listhub_houses_start_date,
    )
    logger.info(f"Total HOUSES => {listhub_houses.count()}")
    for house in listhub_houses:
        update_house_main_photo.delay(house.id)
    logger.info(
        "FINISHED queuing the tasks for the FIX for main_photo of listhub listing houses."
    )


@app.task
def update_house_main_photo(house_id):
    logger = logging.getLogger("django")
    try:
        house = House.objects.get(id=house_id)
        house.update_main_photo()
    except House.DoesNotExist:
        logger.debug(f"ERROR => House with id {house_id} does not exist")
    except Exception as e:
        logger.debug(
            f"ERROR => House with id {house_id} could not be updated due to: {e}."
        )


@app.task
def show_house_interest_from_steves_account():
    steve = ApplicationUser.objects.get(email="steve.pharr@agentloop.us")
    house_interest_done_by_steve = Interest.objects.filter(user=steve).values_list(
        "house_id", flat=True
    )
    steves_house = House.objects.filter(user=steve).values_list("id", flat=True)
    houses = (
        House.objects.filter(listing_type="listhublisting")
        .filter(~Q(id__in=house_interest_done_by_steve) & ~Q(id__in=steves_house))
        .select_related("user")
    )
    agent1_houses = houses.filter(user__agent_type="agent1").distinct()
    agent2_houses = houses.filter(user__agent_type="agent2").distinct()
    agent3_houses = houses.filter(user__agent_type="agent3").distinct()

    for house in agent1_houses[:300]:
        process_house_interest.apply_async(
            (house.id, house.user.id, steve.id),
            eta=datetime.now(timezone.utc) + timedelta(minutes=1),
        )
    for house in agent2_houses[:300]:
        process_house_interest.apply_async(
            (house.id, house.user.id, steve.id),
            eta=datetime.now(timezone.utc) + timedelta(hours=2),
        )
    for house in agent3_houses[:300]:
        process_house_interest.apply_async(
            (house.id, house.user.id, steve.id),
            eta=datetime.now(timezone.utc) + timedelta(hours=2),
        )


@app.task
def process_house_interest(house_id, agent_id, steves_id):
    agent = ApplicationUser.objects.get(id=agent_id)
    steve = ApplicationUser.objects.get(id=steves_id)
    house = House.objects.get(id=house_id)
    if not Interest.objects.filter(user=steve, house=house).exists():
        Interest.objects.create(
            user_id=steves_id,
            house_id=house_id,
            interest=Interest.INTEREST_YES,
            system_generated=True,
        )
        street_address = construct_street_address(house)
        unsubscribe_url = construct_unsubscribe_url(agent)
        if agent.agent_type == "agent2":
            print(agent.houses.count(), agent.full_name, agent.agent_type, agent.id)
            updated_house = process_image(house)
            login_redirect_url = construct_login_url(agent.first_name)
            send_templated_mail(
                user=agent,
                template_name="steve_house_interest_in_a2_listhub_property.html",
                from_email="AgentLoop<invitations@agentloop.us>",
                recipient_list=[agent.email],
                context={
                    "total_house": 1,
                    "total_interest": 1,
                    "receiver_firstname": agent.first_name,
                    "receiver_phone": str(agent.phone),
                    "receiver_password": agent.temp_password,
                    "receiver_profile": agent.avatar.url if agent.avatar else "",
                    "property_address": [street_address],
                    "house_image": updated_house.main_photo_with_avatar.url,
                    "unsubscribe_url": unsubscribe_url,
                    "login_redirect_url": login_redirect_url,
                    "subject_name": f"You have new interest on {street_address}",
                    "email_type": "steve_house_interest_a2",
                },
                system_generated=True,
                sender=steve,
            )
        elif agent.agent_type == "agent3":
            print(agent.full_name, agent.agent_type, agent.id)
            updated_house = process_image(house)
            login_redirect_url = construct_login_url(agent.first_name)
            send_templated_mail(
                user=agent,
                template_name="steve_house_interest_in_a3_listhub_property.html",
                from_email="AgentLoop<invitations@agentloop.us>",
                recipient_list=[agent.email],
                context={
                    "total_house": 1,
                    "total_interest": 1,
                    "receiver_firstname": agent.first_name,
                    "receiver_profile": agent.avatar.url if agent.avatar else "",
                    "property_address": [street_address],
                    "house_image": updated_house.main_photo_with_avatar.url,
                    "unsubscribe_url": unsubscribe_url,
                    "login_redirect_url": login_redirect_url,
                    "subject_name": f"You have new interest on {street_address}",
                    "email_type": "steve_house_interest_a3",
                },
                system_generated=True,
                sender=steve,
            )


def construct_street_address(house):
    street = str(house.street)
    if street.startswith(house.street_number):
        street = street.replace(house.street_number, "")
    return f"{house.street_number} {street.lstrip()}"


def process_image(house):
    img_processor = ImageProcessor()
    return img_processor.add_logo(house)


def construct_unsubscribe_url(agent):
    domain = Site.objects.get_current().domain
    return domain + reverse(
        "following:unsubscribe_connection", kwargs={"uuid": agent.uuid}
    )
