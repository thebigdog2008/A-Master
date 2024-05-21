from django.db.models import Q

from realtorx.custom_auth.models import ApplicationUser
from realtorx.houses.models import SavedFilter, House


from django.core.management.base import BaseCommand
import logging

logger = logging.getLogger("django.list_hub")


class Command(BaseCommand):
    def _collect_city_postcode_dict(self, queryset_user_cities):
        """
        returns [
            {
                "city": 989898
            },
            ...
        ]
        """
        _cities_list = []
        _city_zip_code_dict = {}

        for city in queryset_user_cities:
            try:
                if city[0]:
                    _cities_list.append(city[0])
            except IndexError:
                continue

        queryset_house_zip_code = House.objects.values("city", "postcode").filter(
            city__in=_cities_list
        )
        for house in queryset_house_zip_code:
            data = {str(house["city"]).lower().capitalize(): house["postcode"]}
            _city_zip_code_dict.update(data)
        return _city_zip_code_dict

    def handle(self, *args, **options):
        update_list_users = []
        create_list_filters = []
        queryset_users = ApplicationUser.objects.filter(
            Q(agent_type="agent2")
            | Q(agent_type="agent3")
            | Q(saved_filters__isnull=True)
        ).order_by("city")
        queryset_user_cities = queryset_users.values_list("city", flat=True).distinct(
            "city"
        )
        city_zip_code_dict = self._collect_city_postcode_dict(queryset_user_cities)

        for user in queryset_users:
            try:
                city = str(user.city[0]).lower().capitalize()
            except IndexError:
                city = None
            try:
                county = str(user.county[0]).lower().capitalize()
            except IndexError:
                county = None
            state = user.state

            if not city:
                city = county if county else None

            zip_code = city_zip_code_dict.get(city, None)
            # there was street written in city, so city record existed but not correct
            # county also can be a city in US, if its correct, we will got zip from county
            # and it means that we need replace city record with county record
            if not zip_code:
                zip_code = city_zip_code_dict.get(county, None)
                if zip_code:
                    city = county

            # agent2 and 3, who hasnt one of values need to be inactive and  they dont need filters
            if not all((city, county, state, zip_code)):
                user.is_active = False
                update_list_users.append(user)
                continue

            user_filter = dict(
                user=user,
                city=[city],
                county=county,
                state=state,
                name="My City",
                action="sell",
                suburbs=[city],
                suburbs_lower=[str(city).lower()],
                zip_code=[zip_code],
                house_types=["House", "Townhouse", "Apartments", "CondosCo-Ops"],
                baths_count_min=0,
                carparks_count_min=0,
                bedrooms_count_min=0,
                price_min=0,
                price_max=50000000,
                land_size_min=0,
                land_size_min_units="sqft",
                land_size_min_m2=0,
                suitable_for_development=False,
            )
            create_list_filters.append(user_filter)
        ApplicationUser.objects.bulk_update(
            update_list_users, ["is_active"], batch_size=1000
        )
        SavedFilter.objects.bulk_create(
            [SavedFilter(**values) for values in create_list_filters], batch_size=1000
        )
