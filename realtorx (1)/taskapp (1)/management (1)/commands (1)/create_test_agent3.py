from django.core.management.base import BaseCommand

from realtorx.agencies.models import AgencyBranch
from realtorx.custom_auth.models import ApplicationUser, BrokerLicence
from realtorx.houses.models import SavedFilter
from django.conf import settings


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="")
        parser.add_argument("first_name", type=str, help="")
        parser.add_argument("last_name", type=str, help="")
        parser.add_argument("agency_name", type=str, nargs="?", default="AgentLoop HQ")

    def handle(self, *args, **kwargs):
        agency_branch = AgencyBranch.objects.filter(
            agency__name=kwargs.get("agency_name")
        ).first()

        user_data = dict(
            email=kwargs.get("email"),
            first_name=kwargs.get("first_name"),
            last_name=kwargs.get("last_name"),
            phone="+11234567777",
            agency_branch=agency_branch,
            agency=agency_branch.agency,
            state=agency_branch.state,
            city=[agency_branch.city],
            county=[agency_branch.county],
            agent_type=ApplicationUser.AGENT_TYPE_CHOICES.agent3,
            agency_branch_state=agency_branch.state,
            agency_branch_city=agency_branch.city,
            agency_branch_county=agency_branch.county,
            temp_password="Agent1234",
            brokerage_phone_number="+11234567893",
        )

        users = ApplicationUser.objects.filter(
            email=kwargs.get("email"), is_superuser=False
        )

        for user in users:
            for house in user.houses.all():
                print(f"deleting house {house}...")
                house.delete()
            print(f"deleting user {user}...")
            user.delete()

        user = ApplicationUser.objects.create(**user_data)

        SavedFilter.objects.create(
            user=user,
            name=SavedFilter.DEFAULT_FILTER_NAME,
            action="sell",
            price_min=0,
            price_max=settings.FILTER_MAX_PRICE,
            baths_count_min=0.0,
            carparks_count_min=0,
            bedrooms_count_min=0,
            state=user.state,
            county=user.county[0],
            city=user.city,
            house_types=[
                "House",
                "Townhouse",
                "Apartments",
                "CondosCo-Ops",
                "Lotsland",
            ],
        )

        BrokerLicence.objects.create(
            user=user,
            number="1234567890",
        )

        print(
            f'Success - agent 3 created with email - {kwargs.get("email")}, phone - {user_data.get("phone")} and temp password - {user_data.get("temp_password")}'
        )
