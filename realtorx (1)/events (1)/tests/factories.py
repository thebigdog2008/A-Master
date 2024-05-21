import random

import factory
from realtorx.custom_auth.tests.factories import UserFactory
from realtorx.events.models import Event


class EventFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    kind = factory.LazyFunction(
        lambda: random.choice(list(dict(Event.EVENT_TYPES).keys()))
    )  # noqa
    initiator = factory.SubFactory(UserFactory)

    class Meta:
        model = Event
