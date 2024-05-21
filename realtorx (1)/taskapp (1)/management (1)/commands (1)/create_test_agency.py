from django.core.management.base import BaseCommand

from realtorx.agencies.models import AgencyBranch, Agency

from datetime import datetime


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "agency_name",
            type=str,
            nargs="?",
            default=f"Test_Agency_{datetime.now().isoformat()}",
        )
        parser.add_argument("branch_phone", type=str, nargs="?", default="+123456789")

    def handle(self, *args, **kwargs):
        agency_data = dict(name=kwargs.get("agency_name"), about="")

        agency = Agency.objects.create(**agency_data)

        print(f"created new agency {agency.id}")

        agency_branch_data = dict(
            address="Agency address",
            city="city",
            zipcode="123456",
            agency=agency,
            branch_phone=kwargs.get("branch_phone"),
        )

        agency_branch = AgencyBranch.objects.create(**agency_branch_data)

        print(f"created new agency branch {agency_branch.id}")
