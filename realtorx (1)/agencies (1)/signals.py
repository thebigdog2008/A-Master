from django.db.models.signals import post_save
from django.dispatch import receiver

from realtorx.agencies.models import Agency
from realtorx.following.models import ConnectionsGroup


@receiver(post_save, sender=Agency)
def change_default_group_name(sender, instance, **kwargs):
    if instance.name_tracker.has_changed("name") is True:
        user_ids = instance.agents.all().values_list("id", flat=True)
        ConnectionsGroup.objects.filter(
            name=instance.name_tracker.previous("name"),
            owner_id__in=user_ids,
        ).update(name=instance.name)
