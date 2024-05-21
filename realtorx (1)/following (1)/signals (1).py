import django
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from realtorx.following.models import FollowingRequest
from realtorx.following.utils import create_groups


@receiver(post_save, sender=FollowingRequest)
def update_following_relation_on_accept(sender, instance, created, *args, **kwargs):
    if created and instance.status == FollowingRequest.REQUEST_STATUS.accepted:
        instance.sender.following.add(instance.recipient)

    if instance.status_tracker.changed:
        if instance.status == FollowingRequest.REQUEST_STATUS.accepted:
            instance.sender.following.add(instance.recipient)
        else:
            instance.sender.following.remove(instance.recipient)


@receiver(post_save, sender=FollowingRequest)
def create_default_connection_group(sender, instance, created, *args, **kwargs):
    if created and instance.status == FollowingRequest.REQUEST_STATUS.accepted:
        create_groups(instance)
    if (
        instance.status_tracker.changed
        and instance.status == FollowingRequest.REQUEST_STATUS.accepted
    ):
        create_groups(instance)


@receiver(post_delete, sender=FollowingRequest)
def update_following_relation_on_remove(sender, instance, *args, **kwargs):
    if instance.status == FollowingRequest.REQUEST_STATUS.accepted:
        instance.sender.following.remove(instance.recipient)


@receiver(post_delete, sender=FollowingRequest)
def update_connection_groups_on_remove(sender, instance, *args, **kwargs):
    if instance.status == FollowingRequest.REQUEST_STATUS.accepted:
        if instance.sender.agency is not None:
            sender_group = instance.sender.owner_groups.filter(
                name=instance.sender.agency.name
            ).first()
            if sender_group:
                sender_group.members.remove(instance.recipient)

        if instance.recipient.agency is not None:
            recipient_group = instance.recipient.owner_groups.filter(
                name=instance.recipient.agency.name
            ).first()
            if recipient_group:
                recipient_group.members.remove(instance.sender)


# request is created, but notification is not sent yet
following_request_created = django.dispatch.Signal(providing_args=["instance"])


# @receiver(post_save, sender=FollowingRequest)
# def send_notification_about_new_following_request(sender, instance, created, *args, **kwargs):
#     if created:
#         following_request_created.send(FollowingRequest, instance=instance)
#         PushNotification.send_new_following_request(instance)
# commented below code to send push notification instantly
# ten_am_est_to_utc = datetime.time(14, 0, 0)
# one_pm_est_to_utc = datetime.time(17, 0, 0)
# four_pm_est_to_utc = datetime.time(20, 0, 0)
# now = datetime.datetime.now()
#
# if now.time() < ten_am_est_to_utc:
#     eta = datetime.datetime(
#         now.year, now.month, now.day,
#         ten_am_est_to_utc.hour, ten_am_est_to_utc.minute, ten_am_est_to_utc.second,
#     )
# elif now.time() >= ten_am_est_to_utc and now.time() < one_pm_est_to_utc:
#     eta = datetime.datetime(
#         now.year, now.month, now.day,
#         one_pm_est_to_utc.hour, one_pm_est_to_utc.minute, one_pm_est_to_utc.second,
#     )
# elif now.time() >= one_pm_est_to_utc and now.time() < four_pm_est_to_utc:
#     eta = datetime.datetime(
#         now.year, now.month, now.day,
#         four_pm_est_to_utc.hour, four_pm_est_to_utc.minute, four_pm_est_to_utc.second,
#     )
# else:
#     date_tomorrow = now + timezone.timedelta(days=1)
#     eta = datetime.datetime(
#         date_tomorrow.year, date_tomorrow.month, date_tomorrow.day,
#         ten_am_est_to_utc.hour, ten_am_est_to_utc.minute, ten_am_est_to_utc.second,
#     )
# if FollowingRequest.objects.filter(recipient=instance.recipient, status='pending').count() <= 1:
#     # Check if the recipient has only one request accept to push notification other send the number
#     # of connection in push notification
#     send_notification_following_request.apply_async(
#         (instance.id,),
#         eta=eta,
#     )


# Not required in first build
# @receiver(post_save, sender=FollowingRequest)
