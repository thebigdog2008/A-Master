from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from realtorx.houses.managers import HouseQuerySet
from realtorx.houses.models.house import House


class SavedFilterQuerySet(QuerySet):
    def apply(self, queryset: HouseQuerySet) -> HouseQuerySet:
        filters = [f for f in [f.get_house_filter_kwargs() for f in self] if f]
        if not filters:
            return queryset.none()

        filter_query = models.Q()
        for f in filters:
            filter_query = filter_query | models.Q(**f)

        return queryset.filter(filter_query)


class SavedFilter(models.Model):
    DEFAULT_FILTER_NAME = "My City"
    MAX_FILTER_SET_AMOUNT_PER_USER = 20
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="saved_filters",
    )
    name = models.CharField(max_length=100)

    action = models.CharField(max_length=10, choices=House.ACTION_TYPES)
    state = models.CharField(max_length=100, null=True, blank=True)
    city = ArrayField(
        models.CharField(max_length=100), default=list, null=True, blank=True
    )
    zip_code = ArrayField(
        models.CharField(max_length=100), default=list, null=True, blank=True
    )

    baths_count_min = models.DecimalField(decimal_places=1, max_digits=3, default=0)
    carparks_count_min = models.DecimalField(decimal_places=1, max_digits=3, default=0)
    bedrooms_count_min = models.DecimalField(decimal_places=1, max_digits=3, default=0)
    price_min = models.IntegerField(null=True, blank=True)
    price_max = models.IntegerField(null=True, blank=True)

    land_size_min_sqft = models.FloatField(null=True, blank=True)

    living_area_min = models.FloatField(null=True, blank=True)

    suitable_for_development = models.BooleanField(default=False)

    objects = SavedFilterQuerySet.as_manager()

    @classmethod
    def apply_all_user_filters(cls, user, queryset: QuerySet) -> QuerySet:
        filters = cls.objects.filter(user=user)

        if filters == models.QuerySet().none():
            return None

        filter_query = models.Q()
        for f in filters:
            filter_query |= models.Q(**f.get_house_filter_kwargs())

        return queryset.filter(filter_query)

    def clean(self):
        if (
            not self.id
            and self._meta.model._default_manager.filter(
                user=self.user,
            ).count()
            >= self.MAX_FILTER_SET_AMOUNT_PER_USER
        ):
            raise ValidationError(
                _(
                    "User should have at most {0} saved filters".format(
                        self.MAX_FILTER_SET_AMOUNT_PER_USER,
                    ),
                ),
            )

    def save(self, **kwargs):
        if self._check_all_in_array_field(self.city):
            self.city = []
        if self._check_all_in_array_field(self.zip_code):
            self.zip_code = []
        self.land_size_min_sqft = self.land_size_min
        self.living_area_min = self.living_area_min

        super().save(**kwargs)

    def _check_all_in_array_field(self, field):
        for item in field:
            if item.lower() == "all":
                return True
        return False

    def get_house_filter_kwargs(self):
        filter_kwargs = {
            "action": self.action,
        }

        if self.zip_code:
            filter_kwargs["postcode__in"] = self.zip_code

        return filter_kwargs
