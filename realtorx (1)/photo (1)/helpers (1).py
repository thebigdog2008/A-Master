import itertools

from realtorx.custom_auth.models import ApplicationUser
from realtorx.houses.models import House


def regenerate_photos():
    # just call save for every photo. thumbnails will be generated automatically based on optimistic strategy

    i = 0

    for photo in itertools.chain(
        itertools.chain(
            *(
                itertools.chain(house.photos.all(), house.floor_plan_photos.all())
                for house in House.objects.all()
            )
        ),
        itertools.chain(*(user.photos.all() for user in ApplicationUser.objects.all())),
    ):
        try:
            photo.save()
            i += 1
            if i % 100 == 0:
                print(i)
        except IOError as ex:
            print(ex)
