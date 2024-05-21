from config import settings
from realtorx.houses.image_processor.image_processor import ImageProcessor
from realtorx.utils.signals import DisableSignals
from django.contrib.auth import get_user_model
from realtorx.mailing.utils import send_templated_mail
from realtorx.houses.models.interest import Interest
from realtorx.custom_auth.models import ApplicationUser
from realtorx.following.models import FollowingRequest
from realtorx.registrations.serializers_common import MakeFollowingListRequestSerializer
from realtorx.taskapp import app
import pytz
from datetime import datetime
from django.utils import timezone
from django.urls import reverse
from django.contrib.sites.models import Site
from realtorx.utils.mixpanel import track_mixpanel_event
from django.db.models import Q
from realtorx.utils.urls import construct_login_url

import logging

logger = logging.getLogger("django.validation_log")

User = get_user_model()


def generate_random_password():
    import string
    import random

    ran = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return ran


def send_email_in_coming_following_requests(user, all_connections):

    connections_all = []
    for follow in all_connections:
        connections_all.append(
            (
                follow.sender.full_name,
                follow.sender.city[0] if follow.sender.city else "",
                follow.sender.agency.name if follow.sender.agency else "",
            )
        )

    if connections_all:
        try:
            city = user.city[0]
        except IndexError:
            city = ""
        domain = Site.objects.get_current().domain
        accept_url = domain + reverse(
            "following:accept_template", kwargs={"uuid": user.uuid}
        )
        unsubscribe_url = domain + reverse(
            "following:unsubscribe_connection", kwargs={"uuid": user.uuid}
        )
        login_redirect_url = construct_login_url(user.first_name)

        send_templated_mail(
            user=user,
            template_name="page3_after_more_then_three_request_for_a2.html",
            from_email="AgentLoop<connect@agentloop.us>",
            recipient_list=[user.email],
            context={
                "user_first_name": user.first_name,
                "user_name": user.full_name,
                "accept_url": accept_url,
                "unsubscribe_url": unsubscribe_url,
                "login_redirect_url": login_redirect_url,
                "user_phone": str(user.phone),
                "user_password": user.temp_password,
                "user_county": user.county[0] if user.county else "",
                "user_state": user.state,
                "user_city": city,
                "connections": connections_all,
                "counter": len(connections_all) - 1,
                "subject_name": "Further Connection Requests",
                "email_type": "page3",
            },
        )


# page 3
@app.task
def send_email_with_in_coming_following_requests():
    agent_2_activity_threshold = datetime(2022, 3, 1, tzinfo=pytz.UTC)
    for user in User.objects.filter(
        send_email_with_temp_password=True,
        in_coming_requests__isnull=False,
        agent_type="agent2",
    ).distinct():
        if not user.houses.filter(
            Q(created__gte=agent_2_activity_threshold)
            | Q(modified__gte=agent_2_activity_threshold)
        ).exists():
            continue
        if (
            not user.connection_email_unsubscribe
            and user.send_email_with_temp_password
            and user.first_login
            and user.user_type == ApplicationUser.TYPE_CHOICES.agent
        ):

            all_connections = user.in_coming_requests.filter(
                status=FollowingRequest.REQUEST_STATUS.pending
            )
            # today = timezone.datetime.today().date()
            # if all_connections.count() >= 3 and user.next_email_date == today:
            if all_connections.count() >= 3:
                # set second email template will call after 7 days.
                # if user.email_counter < 2:
                #     week_ago = today + timezone.timedelta(days=7)
                #     user.next_email_date = week_ago
                #     user.email_counter += 1
                # elif user.email_counter >= 2:
                #     week_ago = today + timezone.timedelta(days=16)
                #     user.next_email_date = week_ago
                #     user.email_counter = 0
                # set the temp password into user password
                if user.temp_password is None:
                    password = generate_random_password()
                    user.set_password(password)
                    user.temp_password = password
                else:
                    user.set_password(user.temp_password)
                user.save()
                send_email_in_coming_following_requests(user, all_connections)


# page 4
@app.task
def send_email_with_list_hub_in_coming_following_requests():

    for user in User.objects.filter(
        in_coming_requests__isnull=False,
        connection_email_unsubscribe=False,
        agent_type="agent3",
    ).distinct():
        all_connections = user.in_coming_requests.filter(
            status=FollowingRequest.REQUEST_STATUS.pending
        )
        if all_connections.count() >= 3:
            connections_all = []
            for follow in all_connections:
                connections_all.append(
                    (
                        follow.sender.full_name,
                        follow.sender.city[0] if follow.sender.city else "",
                        follow.sender.agency.name if follow.sender.agency else "",
                    )
                )

            domain = Site.objects.get_current().domain
            unsubscribe_url = domain + reverse(
                "following:unsubscribe_connection", kwargs={"uuid": user.uuid}
            )
            login_redirect_url = construct_login_url(user.first_name)

            if connections_all:
                send_templated_mail(
                    user=user,
                    template_name="page4_after_more_then_three_request_for_a3.html",
                    from_email="AgentLoop<connect@agentloop.us>",
                    recipient_list=[user.email],
                    context={
                        "user_first_name": user.first_name,
                        "connections": connections_all,
                        "counter": len(connections_all) - 1,
                        "unsubscribe_url": unsubscribe_url,
                        "login_redirect_url": login_redirect_url,
                        "subject_name": "Further Connection Requests",
                        "email_type": "page4",
                    },
                )


@app.task
def send_email_with_in_coming_following_requests_without_password():

    for user in User.objects.filter(
        send_email_with_temp_password=False,
        connection_email_unsubscribe=False,
        in_coming_requests__isnull=False,
    ).distinct():

        connections = user.in_coming_requests.filter(
            status=FollowingRequest.REQUEST_STATUS.pending,
        ).values_list("sender__first_name", "sender__last_name")
        if connections:
            send_templated_mail(
                user=user,
                template_name="following_requests_without_password",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                context={
                    "user_fullname": user.full_name,
                    "connections": list(connections),
                    "email_type": "following_requests_without_password",
                },
            )


# page 1
@app.task(soft_time_limit=7200, time_limit=8000)
def send_connection_request_email_to_agent2(
    sender_id, recipient_id, system_generated=False
):  # NOTE: system generated meaning connection is being sent from steves account through task in batch

    sender = ApplicationUser.objects.filter(id=sender_id, agent_type="agent1").first()
    recipient = ApplicationUser.objects.filter(
        id=recipient_id, agent_type="agent2"
    ).first()

    if (
        recipient and not recipient.connection_email_unsubscribe
    ):  # and recipient.send_email_with_temp_password and recipient.first_login and recipient.user_type == ApplicationUser.TYPE_CHOICES.agent:

        all_connections = recipient.in_coming_requests.filter(
            status=FollowingRequest.REQUEST_STATUS.pending
        )

        # todo: figure out what is going on here
        if all_connections.count() <= 3 or system_generated:

            if all_connections.count() == 3:
                today = timezone.datetime.today().date()
                # set second email template will call after 7 days.
                week_ago = today + timezone.timedelta(days=7)
                recipient.next_email_date = week_ago

            # set the temp password into user password
            if recipient.temp_password is None:
                password = generate_random_password()
                recipient.set_password(password)
                recipient.temp_password = password
            else:
                recipient.set_password(recipient.temp_password)

            recipient.save()

            try:
                user_city = recipient.city[0]
            except IndexError:
                user_city = ""
            try:
                receiver_city = sender.city[0]
            except IndexError:
                receiver_city = ""

            domain = Site.objects.get_current().domain
            accept_url = domain + reverse(
                "following:accept_template", kwargs={"uuid": recipient.uuid}
            )
            unsubscribe_url = domain + reverse(
                "following:unsubscribe_connection", kwargs={"uuid": recipient.uuid}
            )
            login_redirect_url = construct_login_url(recipient.first_name)

            send_templated_mail(
                user=recipient,
                template_name="page1_connection_request_a1_to_a2.html",
                from_email=f"{sender.full_name}<invitations@agentloop.us>",
                recipient_list=[recipient.email],
                context={
                    "user_first_name": recipient.first_name,
                    "user_name": recipient.full_name,
                    "accept_url": accept_url,
                    "unsubscribe_url": unsubscribe_url,
                    "login_redirect_url": login_redirect_url,
                    "user_phone": str(recipient.phone),
                    "user_county": recipient.county[0] if recipient.county else "",
                    "user_state": recipient.state,
                    "user_city": user_city,
                    "sender_name": sender.full_name,
                    "sender_agency": sender.agency.name,
                    "receiver_city": receiver_city,
                    "sender_phone": str(sender.phone),
                    "sender_profile": sender.avatar.url if sender.avatar else "",
                    "subject_name": "Lets Connect",
                    "receiver_password": recipient.temp_password,
                    "email_type": "page1",
                },
                system_generated=system_generated,
                sender=sender,
            )


# page 2
@app.task(soft_time_limit=7200, time_limit=8000)
def send_connection_request_email_to_agent3(
    sender_id, recipient_id, system_generated=False
):  # NOTE: system generated meaning connection is being sent from steves account through task in batch

    recipient = ApplicationUser.objects.filter(
        id=recipient_id, agent_type="agent3"
    ).first()
    sender = ApplicationUser.objects.filter(id=sender_id, agent_type="agent1").first()

    if recipient and not recipient.connection_email_unsubscribe:

        all_connections = recipient.in_coming_requests.filter(
            status=FollowingRequest.REQUEST_STATUS.pending
        )

        if all_connections.count() <= 3 or system_generated:

            domain = Site.objects.get_current().domain
            unsubscribe_url = domain + reverse(
                "following:unsubscribe_connection", kwargs={"uuid": recipient.uuid}
            )
            login_redirect_url = construct_login_url(recipient.first_name)

            send_templated_mail(
                user=recipient,
                template_name="page2_connection_request_a1_to_a3.html",
                from_email=f"{sender.full_name}<invitations@agentloop.us>",
                recipient_list=[recipient.email],
                context={
                    "user_first_name": recipient.first_name,
                    "sender_fullname": sender.full_name,
                    "sender_agency": sender.agency.name,
                    "sender_phone": str(sender.phone),
                    "sender_profile": sender.avatar.url if sender.avatar else "",
                    "unsubscribe_url": unsubscribe_url,
                    "login_redirect_url": login_redirect_url,
                    "subject_name": "Lets Connect",
                    "email_type": "page2",
                },
                system_generated=system_generated,
                sender=sender,
            )


@app.task(soft_time_limit=7200, time_limit=8000)
def send_follow_request(queryset, user_id):
    queryset = ApplicationUser.objects.filter(id__in=queryset)
    sender = ApplicationUser.objects.get(id=user_id)
    agent_2_activity_threshold = datetime(2022, 3, 1, tzinfo=pytz.UTC)

    agent_1_receiver_count = 0
    agent_2_email_receiver_count = 0
    agent_2_email_skipped_receiver_count = 0
    agent_3_email_receiver_count = 0
    recipient_data = {"email": [], "uuid": [], "agent_type": []}

    for recipient in queryset:
        foll_ser = MakeFollowingListRequestSerializer(
            data={"sender": user_id, "recipient": recipient.id}
        )
        if not foll_ser.is_valid():
            continue
        foll_ser.save()

        recipient_data["email"].append(recipient.email)
        recipient_data["uuid"].append(str(recipient.uuid))
        recipient_data["agent_type"].append(recipient.agent_type)

        track_mixpanel_event(
            str(sender.uuid),
            "new_connection_request_receiver",
            {
                "sender_email": sender.email,
                "recipient_email": recipient.email,
                "sender_uuid": str(sender.uuid),
                "recipient_uuid": str(recipient.uuid),
                "sender_agent_type": sender.agent_type,
                "recipient_agent_type": recipient.agent_type,
            },
        )

        if recipient.agent_type == "agent1":
            agent_1_receiver_count += 1
        elif recipient.agent_type == "agent3":
            send_connection_request_email_to_agent3.delay(user_id, recipient.id)
            agent_3_email_receiver_count += 1
        elif recipient.agent_type == "agent2":
            if recipient.houses.filter(
                Q(created__gte=agent_2_activity_threshold)
                | Q(modified__gte=agent_2_activity_threshold)
            ).exists():
                send_connection_request_email_to_agent2.delay(user_id, recipient.id)
                agent_2_email_receiver_count += 1
            else:
                agent_2_email_skipped_receiver_count += 1

    track_mixpanel_event(
        str(sender.uuid),
        "new_connection_request_sender",
        {
            "sender_email": sender.email,
            "recipient_email": recipient_data["email"],
            "sender_uuid": str(sender.uuid),
            "recipient_uuid": recipient_data["uuid"],
            "sender_agent_type": sender.agent_type,
            "recipient_agent_type": recipient_data["agent_type"],
            "agent_1_recipient_count": agent_1_receiver_count,
            "agent_2_recipient_count": agent_2_email_receiver_count,
            "agent_2_recipient_skipped_count": agent_2_email_skipped_receiver_count,
            "agent_3_recipient_count": agent_3_email_receiver_count,
            "case": "multiple connections",
        },
    )


# page 5 + page 17
# sneakpeeks_or_amazing_listing_agent1_to_agent2s_present_filter
@app.task
def send_instance_email_of_sneakpeeks_or_amazing_agent1_to_agent2(users, house):
    logger.info(
        "send_instance_email_of_sneakpeeks_or_amazing_agent1_to_agent2 function triggered"
    )
    from realtorx.custom_auth.models import ApplicationUser
    from realtorx.houses.models.house import House

    house_obj = House.objects.get(id=house)
    logger.info("newly created house_obj - {}".format(house_obj))

    whitelist_user = ApplicationUser.objects.filter(
        id__in=users, connection_email_unsubscribe=False, agent_type="agent2"
    )

    logger.info("whitelist_users for the new house - {}".format(whitelist_user))

    agent_2_activity_threshold = datetime(2022, 3, 1, tzinfo=pytz.UTC)

    # whitelist_user = house_obj.whitelist.filter(first_login=True, user_type=ApplicationUser.TYPE_CHOICES.agent,
    #                                             is_superuser=False)

    try:
        house_city = house_obj.city
    except IndexError:
        house_city = ""
    try:
        sender_city = house_obj.user.city[0]
    except IndexError:
        sender_city = ""

    logger.info("house_city of the house - {}".format(house_city))
    logger.info("sender_city of the house- {}".format(sender_city))

    email_type = "page_5_page_17"  # default email type

    template, from_email, subject = "", "", ""
    if house_obj.listing_type == House.LISTING_TYPES.minutelisting:
        template = "page5_sneakpeeks_to_matching_A2_agents.html"
        from_email = f"{house_obj.user.full_name}<invitations@agentloop.us>"
        subject = f"SneakPeek of new listing in {house_city}"
        email_type = "page5"
    elif house_obj.listing_type == House.LISTING_TYPES.amazinglisting:
        template = "page17_amazing_Property_to_matching_A2_agents.html"
        from_email = "Amazing Property<invitations@agentloop.us>"
        subject = "Yet to list, but just might be VERY soon."
        email_type = "page17"

    logger.info("email template - {}".format(template))
    logger.info("from_email for the email - {}".format(from_email))
    logger.info("subject for the email - {}".format(subject))

    for user in whitelist_user:
        logger.info("white user for the new house - {}".format(user))
        logger.info("id of the user - {}".format(user.id))
        if not user.houses.filter(
            Q(created__gte=agent_2_activity_threshold)
            | Q(modified__gte=agent_2_activity_threshold)
        ).exists():
            logger.info("Skipping sending of email for user id - {}".format(user.id))
            continue
        if user.temp_password is None:
            password = generate_random_password()
            user.set_password(password)
            user.temp_password = password
        else:
            user.set_password(user.temp_password)
        user.save()

        domain = Site.objects.get_current().domain
        unsubscribe_url = domain + reverse(
            "following:unsubscribe_connection", kwargs={"uuid": user.uuid}
        )
        login_redirect_url = construct_login_url(user.first_name)

        logger.info("domain url - {}".format(domain))
        logger.info("unsubscribe_url - {}".format(unsubscribe_url))

        logger.info("settings.APP_NAME - {}".format(settings.APP_NAME))

        send_templated_mail(
            user=user,
            template_name=template,
            from_email=from_email,
            recipient_list=[user.email],
            context={
                "sender_fullname": house_obj.user.full_name,
                "sender_city": sender_city,
                "sender_phone": str(house_obj.user.phone),
                "sender_agency": house_obj.user.agency.name,
                "sender_profile": (
                    house_obj.user.avatar_thumbnail_square.url
                    if house_obj.user.avatar_thumbnail_square
                    else ""
                ),
                "city": house_city,
                "receive_first_name": user.first_name,
                "receive_phone": str(user.phone),
                "receive_password": user.temp_password,
                "house_image": house_obj.main_photo_email_url,
                "unsubscribe_url": unsubscribe_url,
                "login_redirect_url": login_redirect_url,
                "subject_name": subject,
                "email_type": email_type,
            },
        )


# page 6 + page 18
# sneakpeeks_or_amazing_listing_agent1_to_agent3s_present_filter
@app.task
def send_instance_email_of_sneakpeeks_or_amazing_agent1_to_agent3(users, house):
    from realtorx.houses.models.house import House

    house_obj = House.objects.get(id=house)

    whitelist_user = ApplicationUser.objects.filter(
        id__in=users, connection_email_unsubscribe=False, agent_type="agent3"
    )
    # whitelist_user = house_obj.list_hub_whitelist.all()

    try:
        house_city = house_obj.city
    except IndexError:
        house_city = ""
    try:
        sender_city = house_obj.user.city[0]
    except IndexError:
        sender_city = ""

    template, from_email, subject = "", "", ""
    email_type = "page_6_page_18"
    if house_obj.listing_type == House.LISTING_TYPES.minutelisting:
        template = "page6_sneakpeeks_to_matching_A3_agents.html"
        from_email = f"{house_obj.user.full_name}<invitations@agentloop.us>"
        subject = f"SneakPeek of new listing in {house_city}"
        email_type = "page6"
    elif house_obj.listing_type == House.LISTING_TYPES.amazinglisting:
        template = "page18_amazing_property_to_matching_A3_agents.html"
        from_email = "Amazing Property<invitations@agentloop.us>"
        subject = "Yet to list, but just might be VERY soon."
        email_type = "page18"

    for user in whitelist_user:
        domain = Site.objects.get_current().domain
        unsubscribe_url = domain + reverse(
            "following:unsubscribe_connection", kwargs={"uuid": user.uuid}
        )
        login_redirect_url = construct_login_url(user.first_name)

        send_templated_mail(
            user=user,
            template_name=template,
            from_email=from_email,
            recipient_list=[user.email],
            context={
                "sender_fullname": house_obj.user.full_name,
                "sender_city": sender_city,
                "sender_phone": str(house_obj.user.phone),
                "sender_agency": house_obj.user.agency.name,
                "sender_profile": (
                    house_obj.user.avatar_thumbnail_square.url
                    if house_obj.user.avatar_thumbnail_square
                    else ""
                ),
                "city": house_city,
                "receive_first_name": user.first_name,
                "house_image": house_obj.main_photo_email_url,
                "unsubscribe_url": unsubscribe_url,
                "login_redirect_url": login_redirect_url,
                "subject_name": subject,
                "email_type": email_type,
            },
        )


# page 7
# Email from AgentLoop to agent 2 regarding daily interest activity of a new listing with last 24 hours
@app.task
def send_email_to_agent2_regarding_daily_interest_activity_of_new_listing():
    from datetime import datetime, timedelta
    from realtorx.houses.models import House

    interested_house = Interest.objects.filter(
        house__user__first_login=True,
        house__user__is_superuser=False,
        house__user__agent_type=ApplicationUser.AGENT_TYPE_CHOICES.agent2,
        house__user__send_email_with_temp_password=True,
        house__user__connection_email_unsubscribe=False,
        interest=Interest.INTEREST_YES,
        modified__date=datetime.today().date() - timedelta(days=1),
        house__status=House.HOUSE_STATUSES.published,
        house__listing_type=House.LISTING_TYPES.listhublisting,
    ).exclude(house__user__user_type=ApplicationUser.TYPE_CHOICES.trial)

    users = set(interested_house.values_list("house__user", flat=True))

    for user_id in users:
        house_qs = House.objects.filter(
            id__in=set(
                interested_house.filter(house__user_id=user_id).values_list(
                    "house", flat=True
                )
            )
        )

        if house_qs.count() > 0:
            house_data = {}
            for house in house_qs:
                interest_count = Interest.objects.filter(
                    house=house,
                    interest=Interest.INTEREST_YES,
                    modified__date=datetime.today().date() - timedelta(days=1),
                ).count()
                house_data[house.id] = interest_count

            sort_houses = sorted(house_data.items(), key=lambda x: x[1], reverse=True)
            total_interest = sum(house_data.values())

            first_three_houses = [i[0] for i in sort_houses[:3]]
            houses = House.objects.filter(id__in=first_three_houses)

            user = ApplicationUser.objects.filter(id=user_id).first()
            if user.temp_password is None:
                password = generate_random_password()
                user.set_password(password)
                user.temp_password = password
            else:
                user.set_password(user.temp_password)
            user.save()

            property_address = []
            for address in houses:
                street = str(address.street)
                if street.startswith(address.street_number):
                    street = street.replace(address.street_number, "")
                street_address = f"{address.street_number} {street.lstrip()}"
                property_address.append(street_address)

            img_processor = ImageProcessor()
            updated_house = img_processor.add_logo(houses[0])

            domain = Site.objects.get_current().domain
            unsubscribe_url = domain + reverse(
                "following:unsubscribe_connection", kwargs={"uuid": user.uuid}
            )
            login_redirect_url = construct_login_url(user.first_name)

            send_templated_mail(
                user=user,
                template_name="page7_interest_activity_with_last_24hours_on_A2_listhub_listing.html",
                from_email="AgentLoop<invitations@agentloop.us>",
                recipient_list=[user.email],
                context={
                    "total_house": house_qs.count(),
                    "total_interest": total_interest,
                    "receiver_firstname": user.first_name,
                    "receiver_phone": str(user.phone),
                    "receiver_password": user.temp_password,
                    "receiver_profile": user.avatar.url if user.avatar else "",
                    "property_address": property_address,
                    "house_image": updated_house.main_photo_with_avatar.url,
                    "unsubscribe_url": unsubscribe_url,
                    "login_redirect_url": login_redirect_url,
                    "subject_name": f"You have new interest on {property_address[0]}",
                    "email_type": "page7",
                },
            )


# page 8
# Email from AgentLoop to agent 3 regarding daily activity of a new listing
@app.task
def send_email_to_agent3_regarding_daily_interest_activity_of_new_listing():
    from datetime import datetime, timedelta
    from realtorx.houses.models import House

    interested_house = Interest.objects.filter(
        house__user__agent_type=ApplicationUser.AGENT_TYPE_CHOICES.agent3,
        house__user__connection_email_unsubscribe=False,
        interest=Interest.INTEREST_YES,
        modified__date=datetime.today().date() - timedelta(days=1),
        house__status=House.HOUSE_STATUSES.published,
        house__listing_type=House.LISTING_TYPES.listhublisting,
    ).exclude(house__user__user_type=ApplicationUser.TYPE_CHOICES.trial)

    users = set(interested_house.values_list("house__user", flat=True))

    for user_id in users:
        house_qs = House.objects.filter(
            id__in=set(
                interested_house.filter(house__user_id=user_id).values_list(
                    "house", flat=True
                )
            )
        )

        if house_qs.count() > 0:
            house_data = {}
            for house in house_qs:
                interest_count = Interest.objects.filter(
                    house=house,
                    interest=Interest.INTEREST_YES,
                    modified__date=datetime.today().date() - timedelta(days=1),
                ).count()
                house_data[house.id] = interest_count

            sort_houses = sorted(house_data.items(), key=lambda x: x[1], reverse=True)
            total_interest = sum(house_data.values())

            first_three_houses = [i[0] for i in sort_houses[:3]]
            houses = House.objects.filter(id__in=first_three_houses)

            user = ApplicationUser.objects.filter(id=user_id).first()
            property_address = []
            for address in houses:
                street = str(address.street)
                if street.startswith(address.street_number):
                    street = street.replace(address.street_number, "")
                street_address = f"{address.street_number} {street.lstrip()}"
                property_address.append(street_address)

            img_processor = ImageProcessor()
            updated_house = img_processor.add_logo(houses[0])

            domain = Site.objects.get_current().domain
            unsubscribe_url = domain + reverse(
                "following:unsubscribe_connection", kwargs={"uuid": user.uuid}
            )
            login_redirect_url = construct_login_url(user.first_name)

            send_templated_mail(
                user=user,
                template_name="page8_interest_activity_with_last_24hours_on_A3_listhub_listing.html",
                from_email="AgentLoop<invitations@agentloop.us>",
                recipient_list=[user.email],
                context={
                    "total_house": house_qs.count(),
                    "total_interest": total_interest,
                    "receiver_firstname": user.first_name,
                    "receiver_profile": user.avatar.url if user.avatar else "",
                    "property_address": property_address,
                    "house_image": updated_house.main_photo_with_avatar.url,
                    "unsubscribe_url": unsubscribe_url,
                    "login_redirect_url": login_redirect_url,
                    "subject_name": f"You have new interest on {property_address[0]}",
                    "email_type": "page8",
                },
            )


# page 9
# receive list-hub property of agent2 whose profile is missing
@app.task
def listhub_property_of_agent2_profile_missing(user, house):
    from realtorx.houses.models import House

    user = ApplicationUser.objects.filter(
        id=user,
        first_login=True,
        is_superuser=False,
        connection_email_unsubscribe=False,
        agent_type="agent2",
    )
    if user:
        user = user.first()
        house = House.objects.filter(id=house).first()

        if user.temp_password is None:
            password = generate_random_password()
            user.set_password(password)
            user.temp_password = password
        else:
            user.set_password(user.temp_password)
        user.save()

        street = str(house.street)
        if street.startswith(house.street_number):
            street = street.replace(house.street_number, "")
        street_address = str(house.street_number) + " " + str(street.lstrip())

        domain = Site.objects.get_current().domain
        unsubscribe_url = domain + reverse(
            "following:unsubscribe_connection", kwargs={"uuid": user.uuid}
        )
        login_redirect_url = construct_login_url(user.first_name)

        img_processor = ImageProcessor()
        updated_house = img_processor.add_logo(house)

        # house.refresh_from_db() # commented as it raises AttributeError('Direct status modification is not allowed')

        send_templated_mail(
            user=user,
            template_name="page9_listhub_property_of_A2_whose_profile_is_missing.html",
            from_email="AgentLoop<invitations@agentloop.us>",
            recipient_list=[user.email],
            context={
                "first_name": user.first_name,
                "address": updated_house.raw_address,
                "city": updated_house.city,
                "phone": str(user.phone),
                "password": user.temp_password,
                "receiver_profile": user.avatar.url if user.avatar else "",
                "house_image": updated_house.main_photo_with_avatar.url,
                "unsubscribe_url": unsubscribe_url,
                "login_redirect_url": login_redirect_url,
                "subject_name": f"Missing profile photo for {street_address}",
                "email_type": "page9",
            },
        )


# page 10
# receive list-hub property of agent3 whose profile is missing
@app.task
def listhub_property_of_agent3_profile_missing(user, house):
    from realtorx.houses.models import House

    user = ApplicationUser.objects.filter(
        id=user, connection_email_unsubscribe=False, agent_type="agent3"
    )

    if user:
        user = user.first()
        house = House.objects.filter(id=house).first()

        street = str(house.street)
        if street.startswith(house.street_number):
            street = street.replace(house.street_number, "")
        street_address = str(house.street_number) + " " + str(street.lstrip())

        domain = Site.objects.get_current().domain
        unsubscribe_url = domain + reverse(
            "following:unsubscribe_connection", kwargs={"uuid": user.uuid}
        )
        login_redirect_url = construct_login_url(user.first_name)

        img_processor = ImageProcessor()
        updated_house = img_processor.add_logo(house)

        # house.refresh_from_db() # commented as it raises AttributeError('Direct status modification is not allowed')

        send_templated_mail(
            user=user,
            template_name="page10_listhub_property_of_A3_whose_profile_is_missing.html",
            from_email="AgentLoop<invitations@agentloop.us>",
            recipient_list=[user.email],
            context={
                "first_name": user.first_name,
                "address": updated_house.raw_address,
                "city": updated_house.city,
                "receiver_profile": user.avatar.url if user.avatar else "",
                "house_image": updated_house.main_photo_with_avatar.url,
                "unsubscribe_url": unsubscribe_url,
                "login_redirect_url": login_redirect_url,
                "subject_name": f"Missing profile photo for {street_address}",
                "email_type": "page10",
            },
        )


# page 11
# List hub listing – Seller/Landlord Login details – A1 agent
@app.task
def listhub_property_of_agent1_seller_landlord(house_id: int):
    from realtorx.houses.models import House

    house = House.objects.filter(id=house_id).first()

    if not house.user.connection_email_unsubscribe:
        street = str(house.street)
        if street.startswith(house.street_number):
            street = street.replace(house.street_number, "")
        street_address = str(house.street_number) + " " + str(street.lstrip())

        domain = Site.objects.get_current().domain
        unsubscribe_url = domain + reverse(
            "following:unsubscribe_connection", kwargs={"uuid": house.user.uuid}
        )
        login_redirect_url = construct_login_url(house.user.first_name)

        send_templated_mail(
            user=house.user,
            template_name="page11_listhub_property_of_agent1_seller_landlord.html",
            from_email="AgentLoop<invitations@agentloop.us>",
            recipient_list=[house.user.email],
            context={
                "first_name": house.user.first_name,
                "street_address": street_address,
                "city": house.city,
                "listing_key": house.listing_key,
                "password": house.password,
                "house_image": house.main_photo_email_url,
                "unsubscribe_url": unsubscribe_url,
                "login_redirect_url": login_redirect_url,
                "subject_name": f"{street_address} client login",
                "email_type": "page11",
            },
        )

        with DisableSignals(
            "realtorx.houses.signals.remember_related_object",
            "realtorx.houses.signals.update_house_main_photo",
            "realtorx.houses.signals.new_listing",
            "realtorx.houses.signals.merge_property",
            "realtorx.houses.signals.new_users_in_whitelist",
            sender=House,
        ):
            house.seller_landlord_email_flag = True
            house.save()


# page 12
# List hub listing – Seller/Landlord Login details – A2 agent
@app.task
def listhub_property_of_agent2_seller_landlord(house_id: int):
    from realtorx.houses.models import House

    house = House.objects.filter(id=house_id).first()

    if not house.user.connection_email_unsubscribe:
        street = str(house.street)
        if street.startswith(house.street_number):
            street = street.replace(house.street_number, "")
        street_address = str(house.street_number) + " " + str(street.lstrip())

        domain = Site.objects.get_current().domain
        unsubscribe_url = domain + reverse(
            "following:unsubscribe_connection", kwargs={"uuid": house.user.uuid}
        )
        login_redirect_url = construct_login_url(house.user.first_name)

        # DISABLED AS PER TICKET - https://smrap.atlassian.net/browse/AL-95
        # send_templated_mail(
        #     user=house.user,
        #     template_name='page12_listhub_property_of_agent2_seller_landlord.html',
        #     from_email=f'AgentLoop<invitations@agentloop.us>',
        #     recipient_list=[house.user.email],
        #     context={
        #         'first_name': house.user.first_name,
        #         'street_address': street_address,
        #         'city': house.city,
        #         'listing_key': house.listing_key,
        #         'password': house.password,
        #         'receiver_profile': house.user.avatar.url if house.user.avatar else '',
        #         'house_image': house.main_photo_email_url,
        #         'unsubscribe_url': unsubscribe_url,
        #         'login_redirect_url': login_redirect_url,
        #         'subject_name': f'{street_address} client login'
        #     },
        # )

        with DisableSignals(
            "realtorx.houses.signals.remember_related_object",
            "realtorx.houses.signals.update_house_main_photo",
            "realtorx.houses.signals.new_listing",
            "realtorx.houses.signals.merge_property",
            "realtorx.houses.signals.new_users_in_whitelist",
            sender=House,
        ):
            house.seller_landlord_email_flag = True
            house.save()


# page 13
# List hub listing – Seller/Landlord Login details – A3 agent
@app.task
def listhub_property_of_agent3_seller_landlord(house_id: int):
    from realtorx.houses.models import House

    house = House.objects.filter(id=house_id).first()

    if not house.user.connection_email_unsubscribe:
        street = str(house.street)
        if street.startswith(house.street_number):
            street = street.replace(house.street_number, "")
        street_address = str(house.street_number) + " " + str(street.lstrip())

        domain = Site.objects.get_current().domain
        unsubscribe_url = domain + reverse(
            "following:unsubscribe_connection", kwargs={"uuid": house.user.uuid}
        )
        login_redirect_url = construct_login_url(house.user.first_name)

        # DISABLED AS PER https://smrap.atlassian.net/browse/AL-95

        # send_templated_mail(
        #     user=house.user,
        #     template_name="page13_listhub_property_of_agent3_seller_landlord.html",
        #     from_email=f"AgentLoop<invitations@agentloop.us>",
        #     recipient_list=[house.user.email],
        #     context={
        #         'first_name': house.user.first_name,
        #         'street_address': street_address,
        #         'city': house.city,
        #         'listing_key': house.listing_key,
        #         'password': house.password,
        #         'receiver_profile': house.user.avatar.url if house.user.avatar else '',
        #         'house_image': house.main_photo_email_url,
        #         'unsubscribe_url': unsubscribe_url,
        #         'login_redirect_url': login_redirect_url,
        #         'subject_name': f"{street_address} client login"
        #     },
        # )

        with DisableSignals(
            "realtorx.houses.signals.remember_related_object",
            "realtorx.houses.signals.update_house_main_photo",
            "realtorx.houses.signals.new_listing",
            "realtorx.houses.signals.merge_property",
            "realtorx.houses.signals.new_users_in_whitelist",
            sender=House,
        ):
            house.seller_landlord_email_flag = True
            house.save()


# page 14
# A1 Agent clicks send to more on a list-hub listing this is what A2 agent receives
@app.task
def instant_send_more_property_of_agent1_to_agent2(users, house):

    users = ApplicationUser.objects.filter(
        id__in=users,
        first_login=True,
        is_superuser=False,
        connection_email_unsubscribe=False,
        send_email_with_temp_password=True,
        agent_type="agent2",
    )
    from realtorx.houses.models import House

    house = House.objects.filter(id=house).first()
    agent_2_activity_threshold = datetime(2022, 3, 1, tzinfo=pytz.UTC)

    street = str(house.street)
    if street.startswith(house.street_number):
        street = street.replace(house.street_number, "")
    street_address = str(house.street_number) + " " + str(street.lstrip())

    for user in users:
        if not user.houses.filter(
            Q(created__gte=agent_2_activity_threshold)
            | Q(modified__gte=agent_2_activity_threshold)
        ).exists():
            continue
        try:
            sender_city = house.user.city[0]
        except IndexError:
            sender_city = ""

        if user.temp_password is None:
            password = generate_random_password()
            user.set_password(password)
            user.temp_password = password
        else:
            user.set_password(user.temp_password)
        user.save()

        domain = Site.objects.get_current().domain
        unsubscribe_url = domain + reverse(
            "following:unsubscribe_connection", kwargs={"uuid": user.uuid}
        )
        login_redirect_url = construct_login_url(user.first_name)

        send_templated_mail(
            user=user,
            template_name="page14_send_more_property_of_A1_to_A2.html",
            from_email=f"{house.user.full_name}<invitations@agentloop.us>",
            recipient_list=[user.email],
            context={
                "receiver_first_name": user.first_name,
                "receiver_phone": str(user.phone),
                "receiver_password": user.temp_password,
                "house_city": house.city,
                "house_image": house.main_photo_email_url,
                "sender_fullname": house.user.full_name,
                "sender_agency": house.user.agency.name,
                "sender_city": sender_city,
                "sender_phone": str(house.user.phone),
                "sender_profile": (
                    house.user.avatar_thumbnail_square.url
                    if house.user.avatar_thumbnail_square
                    else ""
                ),
                "unsubscribe_url": unsubscribe_url,
                "login_redirect_url": login_redirect_url,
                "subject_name": f"New listing {street_address}",
                "email_type": "page14",
            },
        )


# page 15
# A1 Agent clicks send to more on a list-hub listing this is what A3 agent receives
@app.task
def instant_send_more_property_of_agent1_to_agent3(users, house):

    users = ApplicationUser.objects.filter(
        id__in=users, connection_email_unsubscribe=False, agent_type="agent3"
    )
    from realtorx.houses.models import House

    house = House.objects.filter(id=house).first()

    street = str(house.street)
    if street.startswith(house.street_number):
        street = street.replace(house.street_number, "")
    street_address = str(house.street_number) + " " + str(street.lstrip())

    for user in users:
        try:
            sender_city = house.user.city[0]
        except IndexError:
            sender_city = ""

        domain = Site.objects.get_current().domain
        unsubscribe_url = domain + reverse(
            "following:unsubscribe_connection", kwargs={"uuid": user.uuid}
        )
        login_redirect_url = construct_login_url(user.first_name)

        send_templated_mail(
            user=user,
            template_name="page15_send_more_property_of_A1_to_A3.html",
            from_email=f"{house.user.full_name}<invitations@agentloop.us>",
            recipient_list=[user.email],
            context={
                "receiver_first_name": user.first_name,
                "house_city": house.city,
                "house_image": house.main_photo_email_url,
                "sender_fullname": house.user.full_name,
                "sender_agency": house.user.agency.name,
                "sender_city": sender_city,
                "sender_phone": str(house.user.phone),
                "sender_profile": (
                    house.user.avatar_thumbnail_square.url
                    if house.user.avatar_thumbnail_square
                    else ""
                ),
                "unsubscribe_url": unsubscribe_url,
                "login_redirect_url": login_redirect_url,
                "subject_name": f"New listing {street_address}",
                "email_type": "page15",
            },
        )


@app.task
def notifify_agent4_on_approval(user_id):
    user = ApplicationUser.objects.get(id=user_id)

    domain = Site.objects.get_current().domain
    unsubscribe_url = domain + reverse(
        "following:unsubscribe_connection", kwargs={"uuid": user.uuid}
    )
    login_redirect_url = construct_login_url(user.first_name)

    send_templated_mail(
        user=user,
        template_name="agent4_agent1_conversion_success.html",
        from_email="<support@agentloop.us>",
        recipient_list=[user.email],
        context={
            "first_name": user.first_name,
            "subject_name": "Your account has been verified",
            "unsubscribe_url": unsubscribe_url,
            "login_redirect_url": login_redirect_url,
            "email_type": "agent4_agent1_conversion_success",
        },
    )
