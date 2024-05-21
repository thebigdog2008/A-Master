from django.db import models
from model_utils import Choices
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from realtorx.custom_auth.models import ApplicationUser


class Statistic(models.Model):
    EVENT_NAME = Choices(
        ("click_call", _("CLICK CALL")),
        ("click_email", _("CLICK EMAIL")),
    )

    statistic_event = models.CharField(max_length=30, choices=EVENT_NAME)
    statistic_count = models.BigIntegerField(default=0)
    created = models.DateField(auto_created=True)

    def __str__(self):
        return self.statistic_event


class AgentCount(TimeStampedModel):
    count = models.BigIntegerField(default=0)
    agent_type = models.CharField(
        max_length=6, default=ApplicationUser.AGENT_TYPE_CHOICES.agent1
    )
