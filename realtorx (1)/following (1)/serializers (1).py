from django.db.models import Q

from rest_framework import serializers

from phonenumber_field.serializerfields import PhoneNumberField
from unicef_restlib.fields import SeparatedReadWriteField
from unicef_restlib.serializers import UserContextSerializerMixin

from realtorx.agencies.models import Agency
from realtorx.custom_auth.models import ApplicationUser
from realtorx.following.models import ConnectionsGroup
from realtorx.houses.utils import get_point_from_address, get_address_from_point
from localflavor.us.us_states import STATE_CHOICES
from django.conf import settings


class FollowerSerializer(UserContextSerializerMixin, serializers.ModelSerializer):
    following_status = serializers.ReadOnlyField()
    following_type = serializers.ReadOnlyField()
    avatar_thumbnail_square = serializers.ReadOnlyField(
        source="avatar_thumbnail_square_url"
    )
    phone = PhoneNumberField(read_only=True)
    agency_name = serializers.CharField(source="agency.name", allow_null=True)
    group_base = serializers.SerializerMethodField(read_only=True)
    user_type = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ApplicationUser
        fields = (
            "uuid",
            "full_name",
            "agency_name",
            "state",
            "county",
            "city",
            "avatar_thumbnail_square",
            "phone",
            "following_status",
            "following_type",
            "group_base",
            "user_type",
            # following request calculated
        )

    def get_group_base(self, obj):
        if (
            obj.agency
            and obj.brokerage_phone_number
            and obj.agency == self.context["request"].user.agency
            and obj.brokerage_phone_number
            == self.context["request"].user.brokerage_phone_number
        ):
            return "Internal"
        if obj.agency and obj.agency == self.context["request"].user.agency:
            return "Company"
        else:
            return "All"

    def get_user_type(self, obj):
        if obj.agent_type != ApplicationUser.AGENT_TYPE_CHOICES.agent3:
            return "Application User"
        else:
            return "ListHub User"


class UsersUUIDSerializer:
    pass


class GroupBaseSerializer(serializers.ModelSerializer):
    members = SeparatedReadWriteField(
        read_field=serializers.SerializerMethodField(read_only=True),
        write_field=serializers.ListField(),
    )
    group_base = serializers.SerializerMethodField(read_only=True)

    def get_members(self, obj):
        return UsersUUIDSerializer(
            obj.all().exclude(Q(is_active=False)), many=True
        ).data

    class Meta:
        model = ConnectionsGroup
        fields = [
            "id",
            "name",
            "members",
            "group_base",
        ]
        read_only_fields = ("id", "members", "group_base")

    def get_group_base(self, obj):
        if Agency.objects.filter(name=obj.name).exists():
            return "Company"
        elif obj.name.endswith("Internal Office"):
            return "Internal"
        else:
            return "Manually"

    def create(self, validated_data):
        owner = self.context.get("request").user
        if len(validated_data["members"]) == 0:
            raise serializers.ValidationError("Members is required.")
        user_ids = ApplicationUser.objects.filter(
            uuid__in=validated_data["members"]
        ).values_list("id", flat=True)
        item = ConnectionsGroup.objects.create(
            owner=owner,
            name=validated_data["name"],
        )
        item.members.add(*user_ids)

        return item


class FilterGroupBaseSerializer(serializers.ModelSerializer):
    members = SeparatedReadWriteField(
        read_field=serializers.SerializerMethodField(read_only=True),
        write_field=serializers.ListField(),
    )

    def get_members(self, obj):
        geocode_address = self.context.get("request").query_params.get(
            "geocode_address", None
        )
        if geocode_address:
            point = get_point_from_address(geocode_address)
            address = get_address_from_point(point)

            if address is not None:
                state = address[4]
                county = address[7]
                city = address[3]
                state = (
                    [item for item in STATE_CHOICES if state in item] if state else ""
                )

        ids = []
        user_data = obj.all().exclude(Q(is_active=False)).values_list("id")
        if user_data:
            for i in user_data:
                ids = ids + list(i)
            user_data = tuple(ids)

        query_params = {
            "current_user": self.context.get("request").user.id,
            "user_data": user_data,
            "state": state[0][0] if state else "",
            "county": county,
            "county1": county.replace(" County", ""),  # update
            "city": "{" + city + "}",
            "category": self.context.get("request").query_params.get("category", None),
            "baths_count": self.context.get("request").query_params.get(
                "baths_count", None
            ),
            "carparks_count": self.context.get("request").query_params.get(
                "carparks_count", None
            ),
            "bedrooms_count": self.context.get("request").query_params.get(
                "bedrooms_count", None
            ),
            "price": (
                0
                if self.context.get("request").query_params.get("price", None)
                in ["", None]
                else self.context.get("request").query_params.get("price", None)
            ),
            "property_type": "{"
            + self.context.get("request").query_params.get("property_type", None)
            + "}",
        }

        sql_query = """ select DISTINCT "custom_auth_applicationuser"."id" , password,
         last_login, is_superuser, brokerage_phone_number, brokerage_address, brokerage_website, display_realtor_logo,
         display_fair_housing_logo, schedule_id, email_notifications_enabled, avatar, phone, verified_user, uuid, username,
         full_name, first_name,last_name, email, "custom_auth_applicationuser"."state", "custom_auth_applicationuser"."county",
         "custom_auth_applicationuser"."city", agency_id, is_staff, is_active, date_joined, date_first_login, first_login,
         send_email_with_temp_password,temp_password, show_splash_screen_login, show_splash_screen_house,
         show_splash_screen_search, "agencies_agency"."id", "agencies_agency"."name","agencies_agency"."about"
         FROM "custom_auth_applicationuser" LEFT OUTER JOIN "houses_savedfilter"on
         ("custom_auth_applicationuser"."id" = "houses_savedfilter"."user_id") LEFT OUTER JOIN "houses_savedfilter" T3 ON
         ("custom_auth_applicationuser"."id" = T3."user_id") INNER JOIN "houses_savedfilter" T5 on
         ("custom_auth_applicationuser"."id" = T5."user_id") LEFT OUTER JOIN "agencies_agency" on
         ("custom_auth_applicationuser"."agency_id" = "agencies_agency"."id")
         WHERE (NOT ("custom_auth_applicationuser"."id" = %(current_user)s)
         AND  "custom_auth_applicationuser"."id" IN %(user_data)s
         AND ("houses_savedfilter"."state" = %(state)s OR UPPER("houses_savedfilter"."state"::text) = UPPER('')
         OR "houses_savedfilter"."state" IS NULL OR UPPER("houses_savedfilter"."state"::text) = UPPER('ALL'))
         AND ((UPPER(T3."county"::text) = UPPER(%(county)s) OR UPPER(T3."county"::text) = UPPER(%(county1)s))
         OR UPPER(T3."county"::text) = UPPER('') OR T3."county" IS NULL OR UPPER(T3."county"::text) = UPPER('ALL'))
         AND (T3."city" && %(city)s::varchar(100)[] OR T3."city" IS NULL OR T3."city" = '{}')
         AND T5."action"::text LIKE %(category)s
         AND (T5."baths_count_min" <= %(baths_count)s OR T5."baths_count_min" IS NULL)
         AND (T5."carparks_count_min" <= %(carparks_count)s OR T5."carparks_count_min" IS NULL)
         AND (T5."bedrooms_count_min" <= %(bedrooms_count)s OR T5."bedrooms_count_min" IS NULL)
         AND (T5."house_types" @> %(property_type)s::varchar(30)[] OR T5."house_types" = '{}' OR T5."house_types" IS NULL)
         AND (T5."price_min" <= %(price)s OR T5."price_min" IS NULL)"""

        price = (
            0
            if self.context.get("request").query_params.get("price", None) in ["", None]
            else self.context.get("request").query_params.get("price", None)
        )
        if int(price) <= settings.FILTER_MAX_PRICE:
            sql_query += (
                """AND (T5."price_max" >= %(price)s OR T5."price_max" IS NULL)"""
            )

        allow_large_dogs = self.context.get("request").query_params.get(
            "allow_large_dogs", None
        )
        if allow_large_dogs:
            large_dogs = "yes" if allow_large_dogs in ["yes", "may_be"] else "no"
            query_params.update({"large_dogs": large_dogs})
            sql_query += """AND (T5."allow_large_dogs"::text = %(large_dogs)s OR T5."allow_large_dogs" IS NULL)"""

        allow_small_dogs = self.context.get("request").query_params.get(
            "allow_small_dogs", None
        )
        if allow_small_dogs:
            small_dogs = "yes" if allow_small_dogs in ["yes", "may_be"] else "no"
            query_params.update({"small_dogs": small_dogs})
            sql_query += """AND (T5."allow_small_dogs"::text = %(small_dogs)s OR T5."allow_small_dogs" IS NULL)"""

        allow_cats = self.context.get("request").query_params.get("allow_cats", None)
        if allow_cats:
            cats = "yes" if allow_cats in ["yes", "may_be"] else "no"
            query_params.update({"cats": cats})
            sql_query += (
                """AND (T5."allow_cats"::text = %(cats)s OR T5."allow_cats" IS NULL)"""
            )

        internal_listing = eval(
            self.context.get("request")
            .query_params.get("internal_listing", "false")
            .title()
        )
        if internal_listing:
            agency = (
                self.context.get("request").user.agency.name
                if self.context.get("request").user.agency.name
                else None
            )
            query_params.update({"agency": agency})
            sql_query += """AND (agencies_agency."name"::text = %(agency)s) """

        sql_query += """) ORDER BY full_name ASC"""

        queryset = ApplicationUser.objects.raw(sql_query, query_params)
        return UsersUUIDSerializer(queryset, many=True).data

    class Meta:
        model = ConnectionsGroup
        fields = [
            "id",
            "name",
            "members",
        ]
        read_only_fields = ("id", "members")


class UserSerializer:
    pass


class GroupSerializer(GroupBaseSerializer):
    members = SeparatedReadWriteField(
        read_field=serializers.SerializerMethodField(),
        write_field=serializers.ListField(),
    )

    def get_members(self, obj):
        return UserSerializer(
            obj.all().exclude(Q(is_active=False)).order_by("full_name"), many=True
        ).data

    # def update(self, instance, validated_data):
    #     members = validated_data.get('members', None)
    #     if members:
    #         validated_data['members'] = ApplicationUser.objects.filter(uuid__in=members).values_list('id', flat=True)
    #     return super().update(instance, validated_data)


class AutoConnectionsSerializer(serializers.Serializer):
    phone_numbers = serializers.CharField(max_length=None, min_length=None)
    phone_number_list = serializers.SerializerMethodField()

    def validate_phone_numbers(self, data):
        # NOTE: If you add any changes in the logic here, also modify the logic at registrations.filters.RegistrationFilterSet
        for _ in (" ", "-", "+", "#", "*", "(", ")"):
            data = data.replace(_, "")
        return "".join(
            f"{phone[-9:]},"
            for phone in data.split(",")
            if (len(phone) >= 9 and phone.isdigit())
        ).rstrip(",")

    def get_phone_number_list(self, obj):
        return obj["phone_numbers"].split(",")
