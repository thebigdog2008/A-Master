from django.core.management.base import BaseCommand
from django.utils import timezone
import datetime
import logging
import requests

from realtorx.crm.listhub import listhub_extraction
from realtorx.crm.models import GlobalState, ListingStatus, ListHubAPILogs

from realtorx.houses.models import House
from realtorx.taskapp.management.commands.get_token_utils import GetTokenCommand

logger = logging.getLogger("django.list_hub")


def collect_listhub_listings(api_url, headers):

    listings = []

    while True:
        results = requests.request("GET", api_url, headers=headers).json()

        if results.get("value"):
            listings += results["value"]

            api_url = results.get("@odata.nextLink")
            if not api_url:
                break
        else:
            break

    return listings


def should_process_listing(listing):

    if not listing.get("Media", []):
        return False

    if listing.get("StandardStatus", "") != "Active":
        return False

    if listing.get("PropertyType") == "Land":
        return False

    # These fields must be present and non-empty
    required_fields = (
        "ListAgentEmail",
        "ListPrice",
        "ListOfficeName",
        "YearBuilt",
    )
    for field in required_fields:
        if not listing.get(field):
            return False

    # Ignore if our db record is up-to-date with Listhub
    if House.objects.filter(
        listing_key=listing["ListingKey"],
        listhub_modification_timestamp=listing["ModificationTimestamp"],
    ).exists():
        return False

    # Otherwise we process it
    return True


class Command(BaseCommand, GetTokenCommand):

    def handle(self, *args, **options):

        task_start_time = timezone.now()

        global_state_instance, _ = GlobalState.objects.get_or_create(
            key="listhub-api-last-fetch-at"
        )
        now = datetime.datetime.now()
        global_state_value = (
            global_state_instance.value
            if global_state_instance.value
            else (now - datetime.timedelta(minutes=100))
        )
        # Note we need this in the API expected format 2022-08-03T00:00:00.000Z thus the + 'Z"
        modification_timestamp_start = (
            global_state_value
            if isinstance(global_state_value, str)
            else str(global_state_value.isoformat()) + "Z"
        )
        modification_timestamp_end = (
            now - datetime.timedelta(minutes=90)
        ).isoformat() + "Z"

        top = 500
        filters = f"Country eq 'US' and PropertyType/any(a:a eq 'Other' and a eq 'Residential') and ModificationTimestamp ge {modification_timestamp_start} and ModificationTimestamp le {modification_timestamp_end}"
        api_url = f"https://api.listhub.com/odata/Property?$count=true&$top={top}&$orderby=ModificationTimestamp asc&$filter={filters}"

        global_state_instance.value = modification_timestamp_end
        global_state_instance.save()

        token = self.get_token()
        headers = {"Authorization": f"Bearer {token}"}
        listings = collect_listhub_listings(api_url, headers)

        # Initialise API log record
        api_log = ListHubAPILogs()
        api_log.task_start_time = task_start_time
        api_log.listhub_timestamp_start = modification_timestamp_start
        api_log.listhub_timestamp_end = modification_timestamp_end
        api_log.api_call = api_url
        api_log.num_listings = len(listings)
        api_log.processed_listings = 0
        api_log.skipped_listings = 0
        api_log.save()

        for listing in listings:

            if should_process_listing(listing):
                listing_status = ListingStatus(
                    listing_key=listing["ListingKey"], url="https://agentloop.us"
                )
                listing_status.save()
                listhub_extraction(listing, listing_status)
                api_log.processed_listings += 1

            else:
                api_log.skipped_listings += 1

            api_log.save()

        # Update API log record
        api_log.task_end_time = timezone.now()
        api_log.task_execution_time = api_log.task_end_time.replace(
            microsecond=0
        ) - api_log.task_start_time.replace(microsecond=0)
        api_log.save()
