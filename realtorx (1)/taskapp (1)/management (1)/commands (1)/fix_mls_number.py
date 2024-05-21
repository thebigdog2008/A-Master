from django.core.management.base import BaseCommand
import logging
from realtorx.houses.models import House

logger = logging.getLogger("django.list_hub")


class Command(BaseCommand):
    def handle(self, *args, **options):
        update_list = []
        error_list = []
        queryset = House.objects.filter(listing_key__isnull=False)
        for house in queryset:
            try:
                mls_number = str(house.listing_key).split("-")[-1]
            except IndexError:
                error_list.append(house.id)
                continue
            house.mls_number = mls_number
            update_list.append(house)
        House.objects.bulk_update(update_list, ["mls_number"], batch_size=1000)
        print(f"updated - {len(update_list)}")
        print(f"error house ids - {error_list}")
