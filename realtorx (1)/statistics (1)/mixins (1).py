from django.contrib.auth import get_user_model
from django.db.models import OuterRef, Q
from django.utils import timezone
from django.utils.functional import cached_property

from psycopg2.extras import DateTimeTZRange

from realtorx.utils.managers import SQCount
from datetime import datetime, timedelta

User = get_user_model()


class StatisticMixin:
    @cached_property
    def statistic_counter(self):
        from realtorx.appointments.models import UserAppointment
        from realtorx.house_chats.models import Chat
        from realtorx.houses.models.interest import Interest

        time_now = timezone.now()
        time_range = (time_now, time_now + timezone.timedelta(microseconds=1))

        statistic = {
            "interested": SQCount(
                Interest.objects.filter(
                    # user_id__in=Subquery(
                    #     # User.objects.filter(following=OuterRef(OuterRef('user_id'))).values_list('id', flat=True),
                    #     User.objects.filter(Q(id=OuterRef('user_id')) | Q(following=OuterRef(OuterRef('user_id')))).values_list('id', flat=True),
                    # ),
                    house_id=OuterRef("id"),
                    interest=Interest.INTEREST_YES,
                )
            ),
            "not_interested": SQCount(
                Interest.objects.filter(
                    # user_id__in=Subquery(
                    #     # User.objects.filter(following=OuterRef(OuterRef('user_id'))).values_list('id', flat=True),
                    #     User.objects.filter(Q(id=OuterRef('user_id')) | Q(following=OuterRef(OuterRef('user_id')))).values_list('id', flat=True),
                    # ),
                    house_id=OuterRef("id"),
                    interest=Interest.INTEREST_NO,
                )
            ),
            "day_interested": SQCount(
                Interest.objects.filter(
                    # user_id__in=Subquery(
                    #     # User.objects.filter(following=OuterRef(OuterRef('user_id'))).values_list('id', flat=True),
                    #     User.objects.filter(Q(id=OuterRef('user_id')) | Q(following=OuterRef(OuterRef('user_id')))).values_list('id', flat=True),
                    # ),
                    house_id=OuterRef("id"),
                    interest=Interest.INTEREST_YES,
                    created__date__gte=(
                        datetime.now() - timedelta(2)
                        if datetime.now().strftime("%A") == "Monday"
                        else datetime.now() - timedelta(1)
                    ),
                )
            ),
            "messages": SQCount(
                Chat.objects.filter(
                    house_id=OuterRef("id"),
                    # creator_id__in=Subquery(
                    #     # User.objects.filter(following=OuterRef(OuterRef('user_id'))).values_list('id', flat=True),
                    #     User.objects.filter(Q(id=OuterRef('creator_id')) | Q(id=OuterRef('recipient_id')) |
                    #                         Q(following=OuterRef(OuterRef('user_id')))).values_list('id', flat=True),
                    # ),
                    has_messages=True,
                )
            ),
            "upcoming_appointments": SQCount(
                UserAppointment.objects.filter(
                    (
                        Q(scheduled_date__contains=DateTimeTZRange(*time_range))
                        | Q(scheduled_date__fully_gt=DateTimeTZRange(*time_range))
                    ),
                    house_id=OuterRef("id"),
                    is_active=True,
                    # sender_id__in=Subquery(
                    #     # User.objects.filter(following=OuterRef(OuterRef('user_id'))).values_list('id', flat=True),
                    #     User.objects.filter(
                    #         Q(id=OuterRef('sender_id')) | Q(following=OuterRef(OuterRef('user_id')))).values_list('id', flat=True),
                    # ),
                )
            ),
        }

        return statistic

    def statistic_querysets(self, house):
        from realtorx.appointments.models import UserAppointment
        from realtorx.house_chats.models import Chat
        from realtorx.houses.models.interest import Interest

        time_now = timezone.now()
        time_range = (time_now, time_now + timezone.timedelta(microseconds=1))

        querysets = {
            "interested": Interest.objects.filter(
                house_id=house,
                interest=Interest.INTEREST_YES,
                # user_id__in=User.objects.filter(following=house.user_id).values_list('id', flat=True),
            ).all(),
            "not_interested": Interest.objects.filter(
                house_id=house,
                interest=Interest.INTEREST_NO,
                # user_id__in=User.objects.filter(following=house.user_id).values_list('id', flat=True),
            ).all(),
            "day_interested": Interest.objects.filter(
                house_id=house,
                interest=Interest.INTEREST_YES,
                created__date__gte=(
                    datetime.now() - timedelta(2)
                    if datetime.now().strftime("%A") == "Monday"
                    else datetime.now() - timedelta(1)
                ),
            ).all(),
            "responses": Interest.objects.filter(
                house_id=house,
                user_id__in=house.sent_to_users.all().values_list("id", flat=True),
            ).all(),
            "messages": Chat.objects.filter(
                house_id=house,
                has_messages=True,
                # creator_id__in=User.objects.filter(following=house.user_id).values_list('id', flat=True),
            ).all(),
            "upcoming_appointments": UserAppointment.objects.filter(
                (
                    Q(scheduled_date__contains=DateTimeTZRange(*time_range))
                    | Q(scheduled_date__fully_gt=DateTimeTZRange(*time_range))
                ),
                is_active=True,
                house_id=house,
                # sender_id__in=User.objects.filter(following=house.user_id).values_list('id', flat=True),
            ).all(),
            "sent_to": house.sent_to_users.all(),
        }
        querysets["no_response"] = (
            querysets["sent_to"]
            .filter(
                ~Q(id__in=querysets["responses"].values_list("user_id", flat=True)),
            )
            .all()
        )

        return querysets
