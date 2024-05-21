from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

import logging

from realtorx.houses.models import House

logger = logging.getLogger("django")


class Command(BaseCommand):
    help = """Populate point field of houses.
        to populate the map for the day
        ./manage.py fix_google_map
    """

    def handle(self, *args, **kwargs):
        time_threshold = timezone.now() - timedelta(hours=24)
        for house in House.objects.filter(
            modified__gt=time_threshold, created_from_listhub=False
        ).exclude(point=None):
            house.save()
            logger.info(f"{house.id} updated point field")
