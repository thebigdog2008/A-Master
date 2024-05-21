from localflavor.us.us_states import STATE_CHOICES

from realtorx.cities.models import City


def parse_address(geocode_result):
    data = {}
    if not geocode_result:
        return "", "", "", "", "", "", ""

    for item in geocode_result[0]["address_components"]:
        for i_type in item["types"]:
            data[i_type] = item["long_name"]

    street_number = data.get("street_number", "")
    street = data.get("route", "")

    administrative_areas = sorted(
        {
            key: value
            for key, value in data.items()
            if "administrative_area_level" in key
        }.items(),
        key=lambda x: int(x[0].split("_")[-1]),
    )

    if not administrative_areas:
        return "", "", "", "", "", "", ""

    if "sublocality" in data:
        suburb = data["sublocality"]
        city = data["sublocality"]
    elif "locality" in data:
        suburb = data["locality"]
        city = data["locality"]
    else:
        suburb = data.get("neighborhood", "")
        city = data.get("neighborhood", "")

    state = administrative_areas[0][1]
    if len(administrative_areas) > 1:
        county = administrative_areas[1][1]
    else:
        county = get_county_by_state_and_city(state, city)

    postcode = "-".join(
        [
            x
            for x in [data.get("postal_code", ""), data.get("postal_code_suffix", "")]
            if x
        ]
    )
    country = data.get("country", "")

    return street_number, street, suburb, city, state, postcode, country, county


def get_county_by_state_and_city(state, city):
    for i_state in STATE_CHOICES:
        if i_state[1] == state:
            try:
                city = City.objects.get(state=i_state[0], name=city)
                return city.county
            except City.DoesNotExist:
                return ""
            except City.MultipleObjectsReturned:
                return City.objects.filter(state=i_state[0], name=city).first().county
    return ""
