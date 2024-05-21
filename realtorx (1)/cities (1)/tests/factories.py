import factory

from realtorx.cities.models import City


class CityFactory(factory.django.DjangoModelFactory):
    state = "LA"
    county = factory.Sequence(lambda n: "Acadia Parish #{n}".format(n=n))
    name = factory.Sequence(lambda n: "Rayne #{n}".format(n=n))
    zip_codes = ["111", "222"]

    class Meta:
        model = City
