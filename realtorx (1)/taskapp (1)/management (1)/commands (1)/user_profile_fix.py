from datetime import datetime, timedelta, timezone
from django.core.management.base import BaseCommand

from realtorx.custom_auth.models import ApplicationUser


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        now = datetime.now(timezone.utc)
        recent_users = ApplicationUser.objects.filter(
            date_joined__gte=(now - timedelta(days=6))
        )
        print("Total USERS => ", recent_users.count())
        updated_users = []
        errored_users = []
        for user in recent_users:
            try:
                user.agency_branch_state = user.state
                user.agency_branch_county = "".join(user.county)
                user.agency_branch_city = "".join(user.city)
                user.save()
                updated_users.append(user)
                print(f"User {user.id} Updated\n")
            except Exception as e:
                print(f"Could not update user {user.id,} due to => ", e, "\n")
                errored_users.append(user)

        print("TOTAL Success =>", len(updated_users))
        print("TOTAL Errored =>", len(errored_users))
