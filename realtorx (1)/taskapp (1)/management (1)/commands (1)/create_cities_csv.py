from django.core.management import BaseCommand

from realtorx.cities.utils import load_file


class Command(BaseCommand):
    DEFAULT = "Zip_Code_database.csv"

    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            "--file",
            help=f"Specify a file containing cities in a CSV format, if not specified, "
            f"{self.DEFAULT} will be chosen instead",
            type=str,
            default=self.DEFAULT,
        )

    def handle(self, file, *args, **options):
        load_file(file)
