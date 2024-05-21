import sys

from django.core.management.base import BaseCommand

from realtorx.custom_auth.models import ApplicationUser
from realtorx.user_schedule.models import Schedule, ScheduleMapping
from realtorx.utils.signals import DisableSignals


def write(message):
    sys.stdout.write("\r\x1b[K")
    sys.stdout.write(message)
    sys.stdout.flush()


def create_schedule(user: ApplicationUser):

    schedule = Schedule.objects.create()
    user.schedule = schedule
    user.save()
    start = "00:00:00"
    end = "23:59:59"
    ScheduleMapping.objects.bulk_create(
        [
            ScheduleMapping(
                day=ScheduleMapping.DAY_NAMES.mon,
                schedule=schedule,
                start=start,
                end=end,
            ),
            ScheduleMapping(
                day=ScheduleMapping.DAY_NAMES.tue,
                schedule=schedule,
                start=start,
                end=end,
            ),
            ScheduleMapping(
                day=ScheduleMapping.DAY_NAMES.wed,
                schedule=schedule,
                start=start,
                end=end,
            ),
            ScheduleMapping(
                day=ScheduleMapping.DAY_NAMES.thu,
                schedule=schedule,
                start=start,
                end=end,
            ),
            ScheduleMapping(
                day=ScheduleMapping.DAY_NAMES.fri,
                schedule=schedule,
                start=start,
                end=end,
            ),
            ScheduleMapping(
                day=ScheduleMapping.DAY_NAMES.sat,
                schedule=schedule,
                start=start,
                end=end,
            ),
            ScheduleMapping(
                day=ScheduleMapping.DAY_NAMES.sun,
                schedule=schedule,
                start=start,
                end=end,
            ),
        ]
    )


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        schedule_query = ApplicationUser.objects.filter(schedule_id__isnull=True)

        num_users_without_schedules = schedule_query.count()

        with DisableSignals(
            "realtorx.custom_auth.receivers.ensure_schedule_exists",
            "realtorx.custom_auth.receivers.check_company",
            "realtorx.custom_auth.receivers.delete_user_without_company_info",
            "realtorx.custom_auth.receivers.create_first_user_filter",
            "realtorx.custom_auth.receivers.create_task_notify_about_persistent_settings",
            sender=ApplicationUser,
        ):

            for count, user in enumerate(schedule_query.all().iterator(), start=1):
                create_schedule(user)
                write(f"Processed {count} of {num_users_without_schedules} users...")

        print()
