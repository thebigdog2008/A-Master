from django.core.management.base import BaseCommand
from datetime import datetime, timedelta

import logging

from realtorx.houses.models import House

logger = logging.getLogger("django")


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        earliest_house_create_date = datetime.now() - timedelta(days=28)
        House.objects.filter(created__lte=earliest_house_create_date).delete()
