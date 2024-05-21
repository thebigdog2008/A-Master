import csv
import os

from django.conf import settings

from realtorx.cities.models import City


def get_header_index(header, name):
    for i, h in enumerate(header):
        if h == name:
            return i
    return -1


def load_file(filename):
    with open(
        os.path.join(settings.BASE_DIR, "realtorx/cities/city_files", filename)
    ) as cities_file:
        reader = csv.reader(cities_file, delimiter=",")

        header = reader.__next__()
        if not header:
            return

        zip_idx = get_header_index(header, "zip")
        state_idx = get_header_index(header, "state")
        county_idx = get_header_index(header, "county")
        city_idx = get_header_index(header, "primary_city")
        timezone_idx = get_header_index(header, "timezone")

        if any(i == -1 for i in [state_idx, county_idx, city_idx]):
            raise Exception(
                "Unable to fine one of the headers. "
                "Please check all columns are in place (state, county, primary_city)"
            )

        cities = {}
        for row in reader:
            city_name = row[city_idx]
            county_name = row[county_idx]
            state = row[state_idx]
            zip = row[zip_idx]
            timezone = row[timezone_idx]

            if not state or not county_name or not city_name:
                continue

            key = (state, county_name, city_name)
            city, created = City.objects.get_or_create(
                state=state,
                county=county_name,
                name=city_name,
                defaults={
                    "zip_codes": [zip],
                    "timezone": timezone,
                },
            )
            if not created and zip not in city.zip_codes:
                city.zip_codes.append(zip)
                city.save()

            cities[key] = {"city": city}

    print(f"updated {len(cities)} cities")
