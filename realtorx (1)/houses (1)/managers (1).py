from django.contrib.auth import get_user_model
from django.db.models import QuerySet, manager
from django.db import models
from django.utils import timezone
from realtorx.statistics.mixins import StatisticMixin
from realtorx.utils.signals import DisableSignals

User = get_user_model()


class HouseQuerySet(StatisticMixin, QuerySet):
    def with_statistic(self):
        return (
            self.with_interested_users_amount()
            .with_not_interested_users_amount()
            .with_day_interested_users_amount()
            .with_chats_amount()
            .with_upcoming_appointments_amount()
        )

    def with_interested_users_amount(self):
        return self.annotate(interested=self.statistic_counter["interested"])

    def with_not_interested_users_amount(self):
        return self.annotate(not_interested=self.statistic_counter["not_interested"])

    def with_day_interested_users_amount(self):
        return self.annotate(day_interested=self.statistic_counter["day_interested"])

    def with_chats_amount(self):
        return self.annotate(messages=self.statistic_counter["messages"])

    def with_upcoming_appointments_amount(self):
        return self.annotate(
            upcoming_appointments=self.statistic_counter["upcoming_appointments"]
        )

    def delete(self):
        from realtorx.houses.models import HousePhoto

        with DisableSignals(
            "realtorx.houses.signals.remember_related_object",
            "realtorx.houses.signals.update_house_main_photo",
            sender=HousePhoto,
        ):
            super().delete()


class HouseManager(StatisticMixin, manager.Manager.from_queryset(HouseQuerySet)):
    def get_queryset_by_statistic_name(self, statistic_name, house):
        return self.statistic_querysets(house).get(statistic_name)


class UserAppointmentQuerySet(QuerySet):
    def for_displaying(self):
        return self.filter(is_active=True)


class PersonalAppointmentManager(
    manager.Manager.from_queryset(UserAppointmentQuerySet)
):
    def get_queryset(self):
        return super().get_queryset().filter(type="personal")


class InspectionTimeManager(models.Manager):
    def get_queryset(self):
        now = timezone.now()
        queryset = super().get_queryset()
        return queryset.filter(end__gt=now)
