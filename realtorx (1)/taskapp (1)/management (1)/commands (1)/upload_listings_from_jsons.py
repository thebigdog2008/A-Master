from django.core.management import BaseCommand

from realtorx.crm.listhub import load_listhub_listings_jsons


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            "--file",
            help="Specify JSONS file containing listings",
            type=str,
            required=False,
        )

    def handle(self, file, *args, **options):
        load_listhub_listings_jsons("listhub.jsons")
