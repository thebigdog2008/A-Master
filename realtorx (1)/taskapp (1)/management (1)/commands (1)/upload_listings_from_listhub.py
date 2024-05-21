from django.core.management import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **options):
        from realtorx.crm.views import get_list_hub_data

        get_list_hub_data()
