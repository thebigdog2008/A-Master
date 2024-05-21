from django.core.management.base import BaseCommand

from realtorx.agencies.models import AgencyBranch
from realtorx.custom_auth.models import ApplicationUser
from realtorx.houses.models import SavedFilter
from django.conf import settings


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="")
        parser.add_argument("first_name", type=str, help="")
        parser.add_argument("last_name", type=str, help="")

    def handle(self, *args, **kwargs):
        agency_branch = AgencyBranch.objects.filter(agency__name="AgentLoop HQ").first()

        user_data = dict(
            email=kwargs.get("email"),
            first_name=kwargs.get("first_name"),
            last_name=kwargs.get("last_name"),
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

        ApplicationUser.objects.filter(
            email=kwargs.get("email"), is_admin=False
        ).delete()

        user = ApplicationUser.objects.create(**user_data)

        filter_ = SavedFilter.objects.create(
            user=user,
            name="Default",
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

        # print(f'Success - use phone - {kwargs.get("phone")} and password Agent1234')
