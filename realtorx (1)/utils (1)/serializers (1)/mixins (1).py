import inspect

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer

from realtorx.cities.models import City


class ModelLevelValidationMixin:
    def model_level_validation(self, data: dict):
        """
        Perform model level validation. In short, call `clean` model method on model instance.

        :param data: fields data
        """

        assert isinstance(
            self, ModelSerializer
        ), "Should be part of `ModelSerializer`"  # noqa

        assert (
            inspect.getouterframes(inspect.currentframe())[1].function == "validate"
        ), "Should be called from `validate` method"  # noqa

        instance = self.Meta.model() if not self.instance else self.instance

        for attr, value in data.items():
            try:
                # skips custom types from a serializer. skips related fields either.
                setattr(instance, attr, value)
            except TypeError:
                continue

        try:
            instance.clean()
        except DjangoValidationError as ex:
            raise ValidationError(ex)


class ValidateRegionMixin:
    def validate_county(self, county):
        if self.initial_data.get("state"):
            state = self.initial_data["state"]
        else:
            state = self.instance.state
        # if not county or not City.objects.filter(county__in=county, state=state).exists():
        #     raise ValidationError(_('Invalid county'))
        if county:
            if not county == [""]:
                if not City.objects.filter(county__in=county, state=state).exists():
                    raise ValidationError(_("Invalid county"))
            if county == [""]:
                county = []
        return county

    def validate_city(self, city):
        """Change str to list country"""
        if type(self.initial_data.get("county")) == str:
            county = [self.initial_data.get("county")]
        else:
            county = self.initial_data.get("county")

        if county:
            county = county
        else:
            county = self.instance.county
        if self.initial_data.get("state"):
            state = self.initial_data["state"]
        else:
            state = self.instance.state
        if city:
            if not city == [""]:
                for c in city:
                    if c.lower() == "all":
                        city.remove(c)

                for c in city[0].split(","):
                    if not City.objects.filter(
                        state=state,
                        county__in=county,
                        name=c,
                    ).exists():
                        raise ValidationError(_("Invalid {city}").format(city=c))
            if city == [""]:
                city = []
        return city
