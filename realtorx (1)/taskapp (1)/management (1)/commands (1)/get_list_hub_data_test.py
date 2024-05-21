from django.core.management.base import BaseCommand
import datetime
import logging
import requests

from realtorx.crm.listhub import test_listhub_extaraction
from realtorx.crm.models import GlobalState, ListingStatus
from realtorx.taskapp.management.commands.get_token_utils import GetTokenCommand

logger = logging.getLogger("django.list_hub")


class Command(BaseCommand, GetTokenCommand):
    def _collect_and_count_listings(self, api_url, headers):
        listings = []
        count = 0
        while True:
            res = requests.request("GET", api_url, headers=headers)
            results = res.json()
            count = count or results.get("@odata.count")

            if results.get("value", ""):
                listings += results["value"]

                next_link = results.get("@odata.nextLink")
                if not next_link:
                    break
                api_url = next_link
            else:
                break

        return listings, count

    def handle(self, *args, **options):
        token = self.get_token()
        headers = {"Authorization": f"Bearer {token}"}
        top = 500

        global_state_instance, _ = GlobalState.objects.get_or_create(
            key="listhub-api-last-fetch-at"
        )
        # Note we need this in the API expected format 2022-08-03T00:00:00.000Z thus the + 'Z"
        now = datetime.datetime.now()
        # modification_timestamp_start = global_state_instance.value if global_state_instance.value else (now - datetime.timedelta(minutes=100)).isoformat() + 'Z'
        modification_timestamp_start = (
            now - datetime.timedelta(minutes=100)
        ).isoformat() + "Z"
        modification_timestamp_end = (
            now - datetime.timedelta(minutes=90)
        ).isoformat() + "Z"

        filters = f"Country eq 'US' and PropertyType/any(a:a eq 'Other' and a eq 'Residential') and ModificationTimestamp ge {modification_timestamp_start} and ModificationTimestamp le {modification_timestamp_end}"
        api_url = f"https://api.listhub.com/odata/Property?$count=true&$top={top}&$orderby=ModificationTimestamp asc&$filter={filters}"

        listings, count = self._collect_and_count_listings(api_url, headers)

        # all listings collected - update last-fetch-at
        # if count:
        #     global_state_instance.value = modification_timestamp_end
        #     global_state_instance.save()

        # TODO delete this once we've done initial testing of these counts

        num_listings = len(listings)
        logger.error(f"Listings Received: {num_listings} out of {count}")

        for listing in listings:
            # check ListAgentEmail, ListPrice and ListOfficeName is not none and check listing status is
            # Active or not
            if (
                len(listing.get("Media", [])) == 0
                or listing.get("StandardStatus", "") != "Active"
            ):
                continue

            if (
                listing["ListAgentEmail"]
                and listing["ListPrice"]
                and listing["ListOfficeName"]
            ):

                listing_status = ListingStatus(
                    listing_key=listing["ListingKey"], url="https://agentloop.us"
                )
                listing_status.save()
                test_listhub_extaraction(listing, listing_status)
