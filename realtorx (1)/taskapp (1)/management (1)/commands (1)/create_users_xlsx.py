from django.core.management import BaseCommand

from realtorx.custom_auth.utils import preloadig_users_from_file


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            "--file",
            help="Specify a file containing users in a XLSX format",
            type=str,
            required=True,
        )

    def handle(self, file, *args, **options):
        preloadig_users_from_file(file)
