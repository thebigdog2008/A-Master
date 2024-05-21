from django.core.management.base import BaseCommand
import csv
import os
from realtorx.custom_auth.models import ApplicationUser
from django.conf import settings


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        disabled_knock_notification_users = ApplicationUser.objects.filter(
            knock_sound_alert=False
        )
        user_count = disabled_knock_notification_users.count()
        print("Total User Count ->", user_count)
        if user_count > 0:
            print("Generating CSV for future reference...")
            with open(
                os.path.join(
                    settings.BASE_DIR, "disabled_knock_notification_users.csv"
                ),
                "a+",
            ) as csvFile:
                writer = csv.DictWriter(
                    csvFile,
                    fieldnames=["id", "agent_type", "date_joined", "email", "phone"],
                )
                for user in disabled_knock_notification_users:
                    writer.writerow(
                        {
                            "id": user.id,
                            "agent_type": user.agent_type,
                            "date_joined": user.date_joined,
                            "email": user.email,
                            "phone": user.phone,
                        }
                    )
            print("CSV created. Updating User Data...")
            disabled_knock_notification_users.update(knock_sound_alert=True)
            print("User Data Updated.\nDone.")
