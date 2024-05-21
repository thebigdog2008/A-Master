from typing import Type

from django.db.models.signals import post_save
from django.dispatch import receiver

from realtorx.events.cache_utils import get_events_cache_key
from realtorx.events.models import Event
from realtorx.following.models import FollowingRequest
from realtorx.following.signals import following_request_created


@receiver(post_save, sender=Event)
def increment_events_count(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.user:
        cache_key = get_events_cache_key(instance.user_id, instance.kind)
        sender.increment_events_count(instance.user.id, instance.kind, cache_key)


def spawn_on_following_request(
    sender: Type[FollowingRequest], instance: FollowingRequest, **kwargs
):
    if instance.recipient:
        Event.objects.create(
            user=instance.recipient,
            initiator=instance.sender,
            kind=Event.EVENT_TYPES.new_connection,
        )


following_request_created.connect(spawn_on_following_request)
