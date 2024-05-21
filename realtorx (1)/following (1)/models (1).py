from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from django_fsm import FSMField, transition
from model_utils import Choices, FieldTracker


class FollowingRequest(models.Model):
    REQUEST_STATUS = Choices(
        ("pending", _("Pending")),
        ("accepted", _("Accepted")),
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="out_coming_requests",
        verbose_name=_("From user"),
        on_delete=models.CASCADE,
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="in_coming_requests",
        verbose_name=_("To user"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    status = FSMField(
        choices=REQUEST_STATUS,
        verbose_name=_("Status"),
        default=REQUEST_STATUS.accepted,  # Set default status to 'accepted'
        protected=True,
    )

    status_tracker = FieldTracker(["status"])
    created = models.DateField(auto_now_add=True)
    system_generated = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return "{sender} ---> {recipient}".format(
            sender=self.sender, recipient=self.recipient
        )

    @transition(status, source=REQUEST_STATUS.pending, target=REQUEST_STATUS.accepted)
    def follow(self):
        self.decrement_events_amount()

    def unfollow(self):
        # do not decrement because of 'accept' implies that decrement already has been occurred
        if self.status != self.REQUEST_STATUS.accepted:
            self.decrement_events_amount()

        self.delete()

    def clean(self):
        if (
            not self.id
            and self._meta.model.objects.filter(
                Q(sender=self.sender, recipient=self.recipient)
                | Q(recipient=self.sender, sender=self.recipient),
            ).exists()
        ):
            raise ValidationError(_("Only one pending or accepted request is allowed."))

        if self.sender == self.recipient:
            raise ValidationError(_("Unable send request to yourself."))


class ConnectionsGroup(models.Model):
    name = models.CharField(max_length=512)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owner_groups"
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="member_groups"
    )

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return f"{self.name}"
