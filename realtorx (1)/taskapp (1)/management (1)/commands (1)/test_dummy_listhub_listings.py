from pathlib import Path
import json

from django.core.management.base import BaseCommand

from realtorx.crm.listhub import listhub_extraction
from realtorx.crm.models import ListingStatus
from datetime import datetime


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "agent2_email", type=str, nargs="?", default="Cat.testing@proton.me"
        )
        parser.add_argument(
            "agent2_listing_address", type=str, nargs="?", default="2 Highland Avenue"
        )
        parser.add_argument("agent2_listing_price", type=int, nargs="?", default=2)
        # parser.add_argument('agent3_email', type=str, nargs='?', default='sarahdougherty77@gmail.com')
        # parser.add_argument('agent3_listing_address', type=str, nargs='?', default='3 Highland Avenue')
        # parser.add_argument('agent3_listing_price', type=int, nargs='?', default=3)

    def handle(self, *args, **kwargs):

        agents = [
            # A3
            # {
            #     'id': 999931,
            #     'email': 'agentloop@proton.me',
            #     'address': '10 Highland Avenue',
            #     'price': 10,
            # },
            # A2
            {
                "id": 1008165,  # This field is not being used
                "email": kwargs.get("agent2_email"),
                "address": kwargs.get("agent2_listing_address"),
                "price": kwargs.get("agent2_listing_price"),
            },
            # A3
            # {
            #     'id': 1008169, #This field is not being used
            #     'email': kwargs.get("agent3_email"),
            #     'address': kwargs.get("agent3_listing_address"),
            #     'price': kwargs.get("agent3_listing_price"),
            # },
            # A1
            # {
            #     'id': 998687,
            #     'email': 'steve.pharr@peergroup.co',
            #     'address': '1 Highland Avenue',
            #     'price': 1,
            # },
        ]

        current_folder = Path(__file__).parent

        with open(current_folder / "dummy_listhub_listing.json", "r") as f:
            listing = json.load(f)

        for agent in agents:

            listing["UnparsedAddress"] = agent["address"]
            listing["ListingKey"] = datetime.now().isoformat()
            listing["ListPrice"] = agent["price"]
            listing["ListAgentEmail"] = agent["email"]

            print("Creating dummy listing:")
            print(agent)

            listing_status = ListingStatus(
                listing_key=listing["ListingKey"], url="https://agentloop.us"
            )
            listing_status.save()
            listhub_extraction(listing, listing_status)
