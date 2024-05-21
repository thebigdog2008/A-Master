import json

from django.core.management.base import BaseCommand
import requests

from realtorx.taskapp.management.commands.get_token_utils import GetTokenCommand


class Command(BaseCommand, GetTokenCommand):

    def add_arguments(self, parser):
        parser.add_argument("listing_key", type=str, help="User id")

    def handle(self, *args, **kwargs):

        listing_key = kwargs["listing_key"]

        token = self.get_token()
        headers = {"Authorization": f"Bearer {token}"}
        api_url = f"https://api.listhub.com/odata/Property('{listing_key}')"

        res = requests.request("GET", api_url, headers=headers)

        results = json.dumps(res.json(), indent=4)

        print(results)
