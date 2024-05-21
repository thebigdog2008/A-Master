from django.core.management.base import BaseCommand
import datetime
import logging
import requests

from realtorx.crm.models import ListingStatus
from realtorx.taskapp.management.commands.get_token_utils import GetTokenCommand

logger = logging.getLogger("django.list_hub")
import time


class Command(BaseCommand, GetTokenCommand):
    def _collect_and_count_listings(self, api_url, headers):
        listings = []
        count = 0
        while True:
            res = requests.request("GET", api_url, headers=headers)
            results = res.json()
            count = count or results.get("@odata.count")
            try:
                listings += results["value"]
            except KeyError as exc:
                print(exc)
                break
            next_link = results.get("@odata.nextLink")
            if not next_link:
                break
            api_url = next_link
            time.sleep(0.1)

        return listings, count

    def handle(self, *args, **options):
        now = datetime.datetime.now()
        modification_timestamp_end = now.isoformat() + "Z"

        urls = [
            # f"https://api.listhub.com/odata/Property?$count=true&$top=500&$orderby=ModificationTimestamp asc&$filter=Country eq 'US' and PropertyType/any(a:a eq 'Other' and a eq 'Residential') and ModificationTimestamp ge 2022-08-26T00:00:00.588561Z and ModificationTimestamp le 2022-08-26T08:00:00.588561Z",
            # f"https://api.listhub.com/odata/Property?$count=true&$top=500&$orderby=ModificationTimestamp asc&$filter=Country eq 'US' and PropertyType/any(a:a eq 'Other' and a eq 'Residential') and ModificationTimestamp ge 2022-08-26T08:00:00.588561Z and ModificationTimestamp le 2022-16-26T16:00:00.588561Z",
            # f"https://api.listhub.com/odata/Property?$count=true&$top=500&$orderby=ModificationTimestamp asc&$filter=Country eq 'US' and PropertyType/any(a:a eq 'Other' and a eq 'Residential') and ModificationTimestamp ge 2022-08-26T16:00:00.588561Z and ModificationTimestamp le 2022-16-26T23:59:59.588561Z",
            "https://api.listhub.com/odata/Property?$count=true&$top=500&$orderby=ModificationTimestamp asc&$filter=Country eq 'US' and PropertyType/any(a:a eq 'Other' and a eq 'Residential') and ModificationTimestamp ge 2022-08-27T00:00:00.588561Z and ModificationTimestamp le 2022-08-27T08:00:00.588561Z",
            "https://api.listhub.com/odata/Property?$count=true&$top=500&$orderby=ModificationTimestamp asc&$filter=Country eq 'US' and PropertyType/any(a:a eq 'Other' and a eq 'Residential') and ModificationTimestamp ge 2022-08-27T08:00:00.588561Z and ModificationTimestamp le 2022-08-27T16:00:00.588561Z",
            "https://api.listhub.com/odata/Property?$count=true&$top=500&$orderby=ModificationTimestamp asc&$filter=Country eq 'US' and PropertyType/any(a:a eq 'Other' and a eq 'Residential') and ModificationTimestamp ge 2022-08-27T16:00:00.588561Z and ModificationTimestamp le 2022-08-27T23:59:59.588561Z",
            "https://api.listhub.com/odata/Property?$count=true&$top=500&$orderby=ModificationTimestamp asc&$filter=Country eq 'US' and PropertyType/any(a:a eq 'Other' and a eq 'Residential') and ModificationTimestamp ge 2022-08-28T00:00:00.588561Z and ModificationTimestamp le 2022-08-28T08:00:00.588561Z",
            "https://api.listhub.com/odata/Property?$count=true&$top=500&$orderby=ModificationTimestamp asc&$filter=Country eq 'US' and PropertyType/any(a:a eq 'Other' and a eq 'Residential') and ModificationTimestamp ge 2022-08-28T08:00:00.588561Z and ModificationTimestamp le 2022-08-28T16:00:00.588561Z",
            "https://api.listhub.com/odata/Property?$count=true&$top=500&$orderby=ModificationTimestamp asc&$filter=Country eq 'US' and PropertyType/any(a:a eq 'Other' and a eq 'Residential') and ModificationTimestamp ge 2022-08-28T16:00:00.588561Z and ModificationTimestamp le 2022-08-28T23:59:59.588561Z",
            "https://api.listhub.com/odata/Property?$count=true&$top=500&$orderby=ModificationTimestamp asc&$filter=Country eq 'US' and PropertyType/any(a:a eq 'Other' and a eq 'Residential') and ModificationTimestamp ge 2022-08-29T00:00:00.588561Z and ModificationTimestamp le 2022-08-29T08:00:00.588561Z",
            "https://api.listhub.com/odata/Property?$count=true&$top=500&$orderby=ModificationTimestamp asc&$filter=Country eq 'US' and PropertyType/any(a:a eq 'Other' and a eq 'Residential') and ModificationTimestamp ge 2022-08-29T08:00:00.588561Z and ModificationTimestamp le 2022-08-29T16:00:00.588561Z",
            "https://api.listhub.com/odata/Property?$count=true&$top=500&$orderby=ModificationTimestamp asc&$filter=Country eq 'US' and PropertyType/any(a:a eq 'Other' and a eq 'Residential') and ModificationTimestamp ge 2022-08-29T16:00:00.588561Z and ModificationTimestamp le 2022-08-29T23:59:59.588561Z",
            "https://api.listhub.com/odata/Property?$count=true&$top=500&$orderby=ModificationTimestamp asc&$filter=Country eq 'US' and PropertyType/any(a:a eq 'Other' and a eq 'Residential') and ModificationTimestamp ge 2022-08-30T00:00:00.588561Z and ModificationTimestamp le 2022-08-30T08:00:00.588561Z",
            "https://api.listhub.com/odata/Property?$count=true&$top=500&$orderby=ModificationTimestamp asc&$filter=Country eq 'US' and PropertyType/any(a:a eq 'Other' and a eq 'Residential') and ModificationTimestamp ge 2022-08-30T08:00:00.588561Z and ModificationTimestamp le 2022-08-30T16:00:00.588561Z",
            "https://api.listhub.com/odata/Property?$count=true&$top=500&$orderby=ModificationTimestamp asc&$filter=Country eq 'US' and PropertyType/any(a:a eq 'Other' and a eq 'Residential') and ModificationTimestamp ge 2022-08-30T16:00:00.588561Z and ModificationTimestamp le 2022-08-30T23:59:59.588561Z",
            "https://api.listhub.com/odata/Property?$count=true&$top=500&$orderby=ModificationTimestamp asc&$filter=Country eq 'US' and PropertyType/any(a:a eq 'Other' and a eq 'Residential') and ModificationTimestamp ge 2022-08-31T00:00:00.588561Z and ModificationTimestamp le 2022-08-31T08:00:00.588561Z",
            f"https://api.listhub.com/odata/Property?$count=true&$top=500&$orderby=ModificationTimestamp asc&$filter=Country eq 'US' and PropertyType/any(a:a eq 'Other' and a eq 'Residential') and ModificationTimestamp ge 2022-08-31T08:00:00.588561Z and ModificationTimestamp le {modification_timestamp_end}",
        ]
        for api_url in urls:
            token = self.get_token()
            headers = {"Authorization": f"Bearer {token}"}
            top = 500

            # global_state_instance, _ = GlobalState.objects.get_or_create(key='listhub-api-last-fetch-at')
            # Note we need this in the API expected format 2022-08-03T00:00:00.000Z thus the + 'Z"

            listings, count = self._collect_and_count_listings(api_url, headers)

            # all listings collected - update last-fetch-at
            # global_state_instance.value = modification_timestamp_end
            # global_state_instance.save()

            # TODO delete this once we've done initial testing of these counts

            num_listings = len(listings)
            logger.error(f"Listings Received: {num_listings} out of {count}")
            for listing in listings:
                # check ListAgentEmail, ListPrice and ListOfficeName is not none and check listing status is
                # Active or not
                if not listing["StandardStatus"] == "Active":
                    continue

                if (
                    listing["ListAgentEmail"]
                    and listing["ListPrice"]
                    and listing["ListOfficeName"]
                ):
                    # create listing status object for sending the data to reverse list hub
                    # TODO figure out if we really need this.  I don't think so but Cam is chicken ;)
                    from realtorx.crm.listhub import listhub_extraction

                    listing_status = ListingStatus(
                        listing_key=listing["ListingKey"], url="https://agentloop.us"
                    )
                    listing_status.save()
                    listhub_extraction(listing, listing_status)
            print(f"done - {api_url}")
            time.sleep(60)
