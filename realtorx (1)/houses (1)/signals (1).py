import pytz
from datetime import datetime, timedelta

from django.db.models import Exists, OuterRef, Q
from django.db.models.signals import (
    m2m_changed,
    post_delete,
    post_save,
    pre_delete,
    pre_save,
)
from django.dispatch import receiver
from django.utils import timezone

from realtorx.custom_auth.models import ApplicationUser
from realtorx.following.models import FollowingRequest
from realtorx.houses.models import House, HousePhoto, Interest, SavedFilter
from realtorx.custom_auth.tasks import (
    send_instance_email_of_sneakpeeks_or_amazing_agent1_to_agent2,
    send_instance_email_of_sneakpeeks_or_amazing_agent1_to_agent3,
)
from realtorx.custom_auth.tasks import (
    instant_send_more_property_of_agent1_to_agent2,
    instant_send_more_property_of_agent1_to_agent3,
)
from realtorx.utils.mixpanel import track_mixpanel_event
from realtorx.following.tasks import process_connection_request
from realtorx.houses.tasks import process_house_interest


@receiver([pre_save, pre_delete], sender=HousePhoto)
def remember_related_object(sender, instance, **kwargs):
    import logging

    logger = logging.getLogger("django.list_hub")

    # instance.content_object will raise AttributeError in post_delete, so just remember it for future usage
    instance.house = instance.content_object
    logger.error(f"\nremember_related_object - {instance.house}")


@receiver(post_save, sender=House)
def new_listing(sender, instance, created, *args, **kwargs):
    import logging

    logger = logging.getLogger("django.validation_log")
    logger.info("\nnew_listing function triggered")
    logger.info("whitelist_users for the new house - {}".format(instance))
    logger.info("newly created house id - {}".format(instance.id))
    logger.info("is the house is created - {}".format(created))

    # NOTE: Check if new mls listing is created first time only and by agent who was not active from datetime.datetime(2022, 3, 1, tzinfo=pytz.UTC)
    # since the agent is active now, a new connection request will be sent to that agent from steve's account

    if created and instance.listing_type == instance.LISTING_TYPES.listhublisting:
        agent_2_activity_threshold = datetime(2022, 3, 1, tzinfo=pytz.UTC)
        user = instance.user
        # TODO bad hardcode
        steve = ApplicationUser.objects.get(email="steve.pharr@agentloop.us")
        if (
            user.agent_type == "agent2"
            and user.houses.filter(Q(created__gte=agent_2_activity_threshold)).count()
            == 1
            and not FollowingRequest.objects.filter(
                recipient=user, sender=steve
            ).exists()
        ):
            process_connection_request.apply_async(
                (
                    user.id,
                    steve.id,
                ),
                eta=datetime.now(timezone.utc) + timedelta(hours=1),
            )

        if Interest.objects.filter(user=steve, house=instance).exists():
            pass
        else:
            if user.agent_type == "agent2" or user.agent_type == "agent3":
                eta = datetime.now(timezone.utc) + timedelta(hours=24)
                process_house_interest.apply_async(
                    (
                        instance.id,
                        user.id,
                        steve.id,
                    ),
                    eta=eta,
                )
            if user.agent_type == "agent1":
                eta = instance.published_at + timedelta(minutes=1)
                process_house_interest.apply_async(
                    (
                        instance.id,
                        user.id,
                        steve.id,
                    ),
                    eta=eta,
                )

    if (
        created or instance.status_tracker.has_changed("status")
    ) and instance.status == instance.HOUSE_STATUSES.published:
        logger.info("\nnew house created and the house is published")
        if instance.listing_type in [
            instance.LISTING_TYPES.minutelisting,
            instance.LISTING_TYPES.amazinglisting,
        ]:

            if instance.listing_type == instance.LISTING_TYPES.minutelisting:
                track_mixpanel_event(
                    str(instance.user.uuid),
                    "sneak_peak_added",
                    {
                        "email": instance.user.email,
                        "phone": str(instance.user.phone),
                        "full_name": instance.user.full_name,
                        "house_address": instance.address,
                        "house_id": str(instance.id),
                    },
                )
            else:
                track_mixpanel_event(
                    str(instance.user.uuid),
                    "amazing_property_added",
                    {
                        "email": instance.user.email,
                        "phone": str(instance.user.phone),
                        "full_name": instance.user.full_name,
                        "house_address": instance.address,
                        "house_id": str(instance.id),
                    },
                )

            from realtorx.custom_auth.tasks import (
                send_instance_email_of_sneakpeeks_or_amazing_agent1_to_agent2,
                send_instance_email_of_sneakpeeks_or_amazing_agent1_to_agent3,
            )

            whitelist_users = list(
                instance.whitelist.all().values_list("id", flat=True)
            )
            logger.info("\nnew house created and the house is published")
            logger.info(
                "whitelist_users before call email function - {}".format(
                    whitelist_users
                )
            )
            send_instance_email_of_sneakpeeks_or_amazing_agent1_to_agent2.delay(
                whitelist_users, instance.pk
            )
            send_instance_email_of_sneakpeeks_or_amazing_agent1_to_agent3.delay(
                whitelist_users, instance.pk
            )

        # Disabled emails 11, 12 and 13 for now.
        # elif instance.listing_type == instance.LISTING_TYPES.listhublisting:
        #     if (
        #         not instance.seller_landlord_email_flag and
        #         instance.user.user_type == ApplicationUser.TYPE_CHOICES.agent and
        #         instance.user.agent_type == ApplicationUser.AGENT_TYPE_CHOICES.agent1
        #     ):
        #         listhub_property_of_agent1_seller_landlord.apply_async(
        #             (instance.id,),
        #             eta=instance.published_at + timedelta(days=1),
        #         )
        #     elif (
        #         not instance.seller_landlord_email_flag and
        #         instance.user.user_type == ApplicationUser.TYPE_CHOICES.agent and
        #         instance.user.agent_type == ApplicationUser.AGENT_TYPE_CHOICES.agent2 and
        #         instance.user.first_login and
        #         not instance.user.connection_email_unsubscribe
        #     ):
        #         listhub_property_of_agent2_seller_landlord.apply_async(
        #             (instance.id,),
        #             eta=instance.published_at + timedelta(days=1),
        #         )
        #     elif (
        #         not instance.seller_landlord_email_flag and
        #         instance.user.user_type == ApplicationUser.TYPE_CHOICES.agent and
        #         instance.user.agent_type == ApplicationUser.AGENT_TYPE_CHOICES.agent3
        #     ):
        #         listhub_property_of_agent3_seller_landlord.apply_async(
        #             (instance.id,),
        #             eta=instance.published_at + timedelta(days=1),
        #         )

        # VLAD: Disabling sending Push notification for now
        # PushNotification.send_new_listing(instance)

    # Check if the saved property is converted from Amazing property to Sneakpeek.
    if (
        instance.listing_tracker.has_changed("listing_type")
        and not created
        and instance.listing_tracker.previous("listing_type")
        == instance.LISTING_TYPES.amazinglisting
        and instance.listing_type == instance.LISTING_TYPES.minutelisting
    ):

        logger.info("\namazing property to sneakpeek conversion push notifications")

        logger.info(
            "updated house - {} and house id - {}".format(instance, instance.id)
        )

        # Get all whitelist users related to the property.
        users = instance.whitelist.all()
        logger.info("house whitelist users - {}".format(users))

        # Get users who have given not interest on the property
        not_interest_user_ids = list(
            Interest.objects.filter(
                house=instance, interest=Interest.INTEREST_NO
            ).values_list("user_id", flat=True)
        )
        logger.info("house not interested users - {}".format(users))

        # Exclude the not interested users.
        users = users.exclude(id__in=not_interest_user_ids)

        logger.info("filtered users to send push notification - {}".format(users))

        logger.info("\nstart delete the interest details for this property")
        # Delete interested details for the updated property.
        Interest.objects.filter(house=instance, interest=Interest.INTEREST_YES).delete()
        logger.info("\nproperty delete interest details completed")
        # Send push notification to whitelist user regarding the property conversion.

@receiver([post_save, post_delete], sender=HousePhoto)
def update_house_main_photo(sender, instance, **kwargs):
    import logging

    logger = logging.getLogger("django.list_hub")
    logger.error("update_house_main_photo ")
    instance.house.update_main_photo()


@receiver(m2m_changed, sender=House.whitelist.through)
def new_users_in_whitelist(sender, action, instance, pk_set, *args, **kwargs):

    house = instance

    if (
        action == "post_add"
        and not house.status_tracker.has_changed("status")
        and house.status == house.HOUSE_STATUSES.published
    ):
        if house.listing_type in [
            house.LISTING_TYPES.minutelisting,
            house.LISTING_TYPES.amazinglisting,
        ]:
            send_instance_email_of_sneakpeeks_or_amazing_agent1_to_agent2.delay(
                list(pk_set), house.pk
            )
            send_instance_email_of_sneakpeeks_or_amazing_agent1_to_agent3.delay(
                list(pk_set), house.pk
            )

        elif house.listing_type == house.LISTING_TYPES.listhublisting:
            # Don't send emails to agents 2 and 3 if we have just pulled this house from ListHub
            just_pulled_from_listhub = getattr(
                house, "_just_pulled_from_listhub", False
            )
            if not just_pulled_from_listhub:
                instant_send_more_property_of_agent1_to_agent2.delay(
                    list(pk_set), house.pk
                )
                instant_send_more_property_of_agent1_to_agent3.delay(
                    list(pk_set), house.pk
                )


# while delete house not change in appointments status

# @receiver(post_save, sender=House)
# def decline_appointments(sender, instance, created, *args, **kwargs):
#     if (
#         instance.status_tracker.has_changed('status')
#         and not instance.status == instance.HOUSE_STATUSES.published
#     ):
#         appointments = UserAppointment.objects.filter(house_id=instance.id, is_active=True).values_list('id', flat=True)
#         decline_appointments_task.delay(list(appointments))


@receiver(post_save, sender=SavedFilter)
def post_filter_save(sender, instance, **kwargs):
    house_ids = filter_based_list_of_houses(instance.user)
    print("+++++------------+++++++++++", house_ids.count())
    events = Event.objects.filter(house_id__in=house_ids, user_id=instance.user_id)
    # modified_house_ids =
    current_user_all_events = Event.objects.filter(
        user_id=instance.user_id
    ).values_list("id", flat=True)
    events_to_be_added = list(
        set(house_ids) - set(events.values_list("house_id", flat=True))
    )
    events_to_be_removed = list(
        set(current_user_all_events) - set(events.values_list("id", flat=True))
    )
    delete_events(events_to_be_removed)
    add_missing_events(events_to_be_added, instance.user_id)


@receiver(post_delete, sender=SavedFilter)
def post_filter_delete(sender, instance, **kwargs):
    try:
        house_ids = filter_based_list_of_houses(instance.user)
        print("+++++------------+++++++++++ delete", house_ids.count())
        events = Event.objects.filter(house_id__in=house_ids, user_id=instance.user_id)
        current_user_all_events = Event.objects.filter(
            user_id=instance.user_id
        ).values_list("id", flat=True)
        events_to_be_added = list(
            set(house_ids) - set(events.values_list("house_id", flat=True))
        )
        events_to_be_removed = list(
            set(current_user_all_events) - set(events.values_list("id", flat=True))
        )
        delete_events(events_to_be_removed)
        # add_missing_events(events_to_be_added,instance.user_id)
    except Exception as e:
        print("---> Exeception", str(e))


def delete_events(events_to_be_removed):
    Event.objects.filter(id__in=events_to_be_removed).delete()


def add_missing_events(events_to_be_added, user_id):
    events = []
    for house_id in events_to_be_added:
        events.append(
            Event(
                user_id=user_id, kind=Event.EVENT_TYPES.new_listing, house_id=house_id
            )
        )
    Event.objects.bulk_create(events)


def filter_based_list_of_houses(user):
    queryset = (
        House.objects.filter(
            status=House.HOUSE_STATUSES.published,
        )
        .select_related("user")
        .exclude(user=user)
        .exclude(main_photo__isnull=True)
        .exclude(main_photo__exact="")
        .annotate(
            interest_exists=Exists(
                Interest.objects.filter(house=OuterRef("id"), user=user).values(
                    "interest"
                ),
            ),
        )
        .filter(
            interest_exists=False,
        )
        .distinct()
    )
    user_filters = SavedFilter.objects.filter(user=user)
    houses = user_filters.apply(queryset)
    past_120_days_datetime = datetime.now(timezone.utc) - timedelta(
        days=House.LISTINGS_DAYS_LIMIT
    )
    # past_120_days_datetime = datetime.now().date() - timedelta(days=
