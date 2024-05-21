from django.shortcuts import render
from realtorx.custom_auth.models import ApplicationUser
from realtorx.houses.models.interest import Interest
from realtorx.house_chats.models import Chat
from realtorx.houses.models.house import House
from datetime import datetime
from realtorx.statistics.models import Statistic
from django.http import HttpResponse


def daily_statistics(request):
    def count_data(today):

        new_account = ApplicationUser.objects.filter(date_joined__date=today).count()

        interest_qs = Interest.objects.filter(modified__date=today)

        interest = interest_qs.filter(interest=2).count()
        not_interest = interest_qs.filter(interest=1).count()

        chats = Chat.objects.filter(created__date=today).count()

        house_qs = House.objects.filter(published_at__date=today)

        amazing_property = house_qs.filter(
            listing_type=House.LISTING_TYPES.amazinglisting
        ).count()
        pre_mls_property = house_qs.filter(
            listing_type=House.LISTING_TYPES.minutelisting
        ).count()

        click_call, created = Statistic.objects.get_or_create(
            statistic_event="click_call", created=today
        )
        click_email, created = Statistic.objects.get_or_create(
            statistic_event="click_email", created=today
        )

        data = {
            "NEW ACCOUNT CREATED": new_account,
            "INTEREST": interest,
            "NOT INTEREST": not_interest,
            "NEW CHAT": chats,
            "AMAZING PROPERTY": amazing_property,
            "SNEEKPEAK PROPERTY": pre_mls_property,
            "CLICK CALL": click_call.statistic_count,
            "CLICK EMAIL": click_email.statistic_count,
        }

        return data

    if request.method == "GET":
        today = datetime.now().date()
        data = count_data(today)
        return render(
            request,
            "statistics/daily_statistics.html",
            context={"data": data, "DATE": today},
        )

    if request.method == "POST":
        today = request.POST["date"]
        data = count_data(today)
        return render(
            request,
            "statistics/daily_statistics.html",
            context={"data": data, "DATE": today},
        )


def statistic_count(request):
    statistics_for = request.GET.get("statistics_for")

    today = datetime.now().date()

    if statistics_for == "click_call":
        event, created = Statistic.objects.get_or_create(
            statistic_event="click_call", created=today
        )
        event.statistic_count = event.statistic_count + 1
        event.save()
        return HttpResponse(status=200)

    if statistics_for == "click_email":
        event, created = Statistic.objects.get_or_create(
            statistic_event="click_email", created=today
        )
        event.statistic_count = event.statistic_count + 1
        event.save()
        return HttpResponse(status=200)

    return HttpResponse(status=400)
