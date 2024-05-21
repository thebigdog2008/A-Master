from typing import TYPE_CHECKING

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.utils.translation import gettext as _

from model_utils import Choices
from realtorx.events.cache_utils import decr, get_events_cache_key

if TYPE_CHECKING:
    from realtorx.custom_auth.models import ApplicationUser


class Event(models.Model):
    EVENT_TYPES = Choices(
        ("unread_thread", _("Unread_thread")),
        ("new_connection", _("New connection")),
        ("new_listing", _("New listing")),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("User"),
        related_name="events",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    kind = models.CharField(
        verbose_name=_("Kind of event"), max_length=50, choices=EVENT_TYPES
    )
    is_viewed = models.BooleanField(verbose_name=_("View state"), default=False)
    created_at = models.DateTimeField(
        verbose_name=_("Creation data"), auto_now_add=True
    )

    initiator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="spawned_events",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
    )
    house = models.ForeignKey(
        "houses.House", on_delete=models.CASCADE, null=True, blank=True
    )

    class Meta:
        ordering = ["id"]

    @classmethod
    def get_unseen_user_events(cls, user_id: int, kind: str, **kwargs):
        return cls.objects.filter(user_id=user_id, is_viewed=False, kind=kind, **kwargs)

    @classmethod
    def get_cached_unseen_events_count(
        cls, user_id: int, by_type: bool = False, **event_filter_fields
    ):
        res = 0 if by_type is False else {}

        for kind in cls.EVENT_TYPES:
            cache_key = get_events_cache_key(user_id, kind[0])
            events_count = cache.get(cache_key)

            if kind[1] == "Unread_thread":
                events_count = Event.objects.filter(
                    user_id=user_id, is_viewed=False, kind=kind[0]
                ).count()
            elif kind[1] == "New connection":
                user = ApplicationUser.objects.filter(id=user_id)
                if len(user) > 0:
                    events_count = ApplicationUser.objects.filter(
                        id__in=user[0]
                        .in_coming_requests.filter(
                            status="pending",
                            sender__is_superuser=False,
                            sender__user_type=ApplicationUser.TYPE_CHOICES.agent,
                        )
                        .all()
                        .values_list("sender_id", flat=True),
                    ).count()
                else:
                    events_count = 0
            elif kind[1] == "New listing":
                events_count = Event.objects.filter(
                    user_id=user_id, is_viewed=False, kind=kind[0]
                ).count()
            else:
                if events_count is None:
                    events_count = cls.set_cached_unseen_events_count(
                        cache_key, user_id, kind[0], **event_filter_fields
                    )

            if not by_type:
                res += events_count
            else:
                res.update({kind[0]: events_count})
        return res

    @classmethod
    def set_cached_unseen_events_count(
        cls, cache_key: str, user_id: int, kind: str, **event_filter_fields
    ):
        events_count = cls.get_unseen_user_events(
            user_id, kind, **event_filter_fields
        ).count()
        cache.set(cache_key, events_count, timeout=None)
        return events_count

    @classmethod
    def increment_events_count(
        cls,
        user_id: int,
        kind: str,
        cache_key: str,
        events_amount: int = 1,
        **event_filter_fields,
    ):
        try:
            cache.incr(cache_key, delta=events_amount)
        except ValueError:
            cls.set_cached_unseen_events_count(
                cache_key, user_id, kind, **event_filter_fields
            )

    @classmethod
    def decrement_events_count(
        cls,
        user_id: int,
        kind: str,
        cache_key: str,
        events_amount: int = 1,
        **event_filter_fields,
    ):
        try:
            decr(cache_key, delta=events_amount)
        except ValueError:
            cls.set_cached_unseen_events_count(
                cache_key, user_id, kind, **event_filter_fields
            )
