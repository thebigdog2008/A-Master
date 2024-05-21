from django.conf import settings
from datetime import datetime, timedelta, timezone
from realtorx.taskapp import app
from realtorx.custom_auth.models import (
    ApplicationUser,
    AndroidPaymentHistory,
    IOSPaymentHistory,
)
from realtorx.houses.models import House
import requests
from requests.auth import HTTPBasicAuth
import json
import urllib.parse
from realtorx.utils.mixpanel import (
    MIXPANEL_EVENT_MESSAGES,
    REVERSE_MIXPANEL_EVENT_MESSAGES,
)
from realtorx.statistics.models import AgentCount

import time
import csv
import tempfile
from django.core.mail import EmailMessage

import logging

logger = logging.getLogger("django.validation_log")

REPORT_RECIPIENTS = (
    "steve@pharr.com.au",
    "udit.jain@opscale.io",
    "anub.sinha@opscale.io",
)


def create_mixpanel_payload(event_names, from_date, to_date, script=None):
    logger.info("create_mixpanel_payload started...")
    if script is None:
        script = 'function main(){{return Events(params).filter(function(event){{return event.properties.environment=="{env}"}}).groupBy(["name"], mixpanel.reducer.count())}}'.format(
            env=settings.APP_ENVIRONMENT
        )
    params = {
        "event_selectors": [],
        "from_date": str(from_date),
        "to_date": str(to_date),
    }
    for event in event_names:
        params["event_selectors"].append({"event": event})
    mixpanel_payload = {"script": script, "params": json.dumps(params)}
    logger.info("create_mixpanel_payload finished.")
    return urllib.parse.urlencode(mixpanel_payload)


def send_mix_panel_request(payload):
    logger.info("send_mix_panel_request started...")
    url = f"https://mixpanel.com/api/2.0/jql?project_id={settings.MIXPANEL_PROJECT_ID}"

    headers = {
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded",
    }

    res = requests.post(
        url,
        data=payload,
        headers=headers,
        auth=HTTPBasicAuth(
            settings.MIXPANEL_SERVICE_ACCOUNT_USERNAME,
            settings.MIXPANEL_SERVICE_ACCOUNT_PASSWORD,
        ),
    )
    if res.status_code != 200:
        print("ERROR in Mixpanel API =>", res.text)
        return None
    logger.info("send_mix_panel_request finished.")
    return res.json()


def get_mixpanel_data(date_start, date_end):
    logger.info("get_mixpanel_data started...")
    mixpanel_events = (
        MIXPANEL_EVENT_MESSAGES["new_connection_request_receiver"],
        MIXPANEL_EVENT_MESSAGES["new_connection_request_sender"],
        MIXPANEL_EVENT_MESSAGES["connection_request_accept"],
        MIXPANEL_EVENT_MESSAGES["property_interest"],
        MIXPANEL_EVENT_MESSAGES["property_not_interested"],
        MIXPANEL_EVENT_MESSAGES["new_self_listing_notification"],
        MIXPANEL_EVENT_MESSAGES["agent3_email_verification_skip"],
    )

    payload = create_mixpanel_payload(mixpanel_events, date_start, date_end)
    response = send_mix_panel_request(payload)

    logger.info("get_mixpanel_data finished.")
    return response


def get_mixpanel_data_email_type(event_type, date_start, date_end):
    logger.info(f"get_mixpanel_data for email_type  started...{event_type}")

    script = 'function main(){{return Events(params).filter(function(event){{return event.properties.environment=="{env}"}}).groupBy(["properties.email_type"], mixpanel.reducer.count())}}'.format(
        env=settings.APP_ENVIRONMENT
    )
    data = {}
    agent_payload = create_mixpanel_payload(
        (MIXPANEL_EVENT_MESSAGES[event_type],), date_start, date_end, script
    )
    response = send_mix_panel_request(agent_payload)
    prefix = "sent" if event_type == "email_sent" else "open"
    for item in response:
        if item["key"][0] is not None:
            data[f"{prefix}_{item['key'][0]}"] = {
                "label": f"{item['key'][0]} email {prefix} in the past 24 hours",
                "value": item["value"],
            }
    return data


def get_mixpanel_data_email_type_link_click(script, date_start, date_end):
    logger.info("get_mixpanel_data for email_type  started...")
    agent_payload = create_mixpanel_payload(
        (MIXPANEL_EVENT_MESSAGES["sendgrid_events"],), date_start, date_end, script
    )
    response = send_mix_panel_request(agent_payload)
    return response[0]["value"] if response else 0


@app.task
def get_email_type_report():
    logger.info("get_email_type_report function triggered")

    now = datetime.now(timezone.utc)
    now_date = now.date()
    yesterday = now - timedelta(days=1)
    yesterday_date = yesterday.date()
    type_sent = get_mixpanel_data_email_type(
        "email_sent", yesterday_date, yesterday_date
    )
    type_opened = get_mixpanel_data_email_type(
        "sendgrid_events", yesterday_date, yesterday_date
    )
    script_button_link = 'function main(){{return Events(params).filter(function(event){{return event.properties.environment=="{env}"&&event.properties.event=="click"&&(event.properties.url.indexOf("{apple_url}")!=-1||event.properties.url.indexOf("{google_url}")!=-1||event.properties.url.indexOf("{button_url}")!=-1) }}).groupBy(["url"], mixpanel.reducer.count())}}'.format(
        apple_url="https://apps.apple.com/us/app/agentloop/id1537126469",
        google_url="https://play.google.com/store/apps/details?id=com.realtorx",
        button_url="https://demo.agentloop.us/ui/store-redirect/",
        env=settings.APP_ENVIRONMENT,
    )
    button_link_clicked = get_mixpanel_data_email_type_link_click(
        script_button_link, yesterday_date, yesterday_date
    )
    script_youtube_link_clicked = 'function main(){{return Events(params).filter(function(event){{return event.properties.environment=="{env}"&&event.properties.event=="click"&&(event.properties.url.indexOf("{youtube_url}")!=-1) }}).groupBy(["url"], mixpanel.reducer.count())}}'.format(
        youtube_url="https://www.youtube.com/watch?", env=settings.APP_ENVIRONMENT
    )
    youtube_link_clicked = get_mixpanel_data_email_type_link_click(
        script_youtube_link_clicked, yesterday_date, yesterday_date
    )
    script_unsubscribe_link_clicked = 'function main(){{return Events(params).filter(function(event){{return event.properties.environment=="{env}"&&event.properties.event=="click"&&(event.properties.url.indexOf("{unsubscribe_url}")!=-1) }}).groupBy(["url"], mixpanel.reducer.count())}}'.format(
        unsubscribe_url="https://demo.agentloop.us/api/following/unsubscribe/",
        env=settings.APP_ENVIRONMENT,
    )
    unsubscribe_link_clicked = get_mixpanel_data_email_type_link_click(
        script_unsubscribe_link_clicked, yesterday_date, yesterday_date
    )
    final_data = {
        **type_sent,
        **type_opened,
        "button_link": {
            "label": "button_link clicked in the past 24 hours",
            "value": button_link_clicked,
        },
        "youtube_link": {
            "label": "youtube_link clicked in the past 24 hours",
            "value": youtube_link_clicked,
        },
        "unsubscribe_link": {
            "label": "unsubscribe_link clicked in the past 24 hours",
            "value": unsubscribe_link_clicked,
        },
    }
    send_report_email.apply_async(
        (final_data, now_date), eta=(now + timedelta(hours=6))
    )  # send report after 6 hours of task start (8pm UTC)


def get_agent_data_mixpanel(start_date, end_date):
    logger.info("get_agent_data_mixpanel started...")

    agent_3_response = get_mixpanel_response_for_agent(
        'function main(){{return Events(params).filter(function(event){{return event.properties.environment=="{env}"&&event.properties.agent_type=="agent3"}}).groupBy(["name"], mixpanel.reducer.count())}}',
        "agent_created",
        start_date,
        end_date,
    )
    agent_3_agent1_conversion_response = get_mixpanel_response_for_agent(
        'function main(){{return Events(params).filter(function(event){{return (event.properties.environment=="{env}"&&event.properties.old_agent_type=="agent3"&&event.properties.new_agent_type=="agent1")}}).groupBy(["name"], mixpanel.reducer.count())}}',
        "agent_type_changed",
        start_date,
        end_date,
    )
    agent_2_agent1_conversion_response = get_mixpanel_response_for_agent(
        'function main(){{return Events(params).filter(function(event){{return (event.properties.environment=="{env}"&&event.properties.old_agent_type=="agent2"&&event.properties.new_agent_type=="agent1")}}).groupBy(["name"], mixpanel.reducer.count())}}',
        "agent_type_changed",
        start_date,
        end_date,
    )
    agent_4_agent1_conversion_response = get_mixpanel_response_for_agent(
        'function main(){{return Events(params).filter(function(event){{return (event.properties.environment=="{env}"&&event.properties.old_agent_type=="agent4"&&event.properties.new_agent_type=="agent1")}}).groupBy(["name"], mixpanel.reducer.count())}}',
        "agent_type_changed",
        start_date,
        end_date,
    )
    agent_4_response = get_mixpanel_response_for_agent(
        'function main(){{return Events(params).filter(function(event){{return (event.properties.environment=="{env}"&&event.properties.old_agent_type=="agent1"&&event.properties.new_agent_type=="agent4")}}).groupBy(["name"], mixpanel.reducer.count())}}',
        "agent_type_changed",
        start_date,
        end_date,
    )
    agent_1_deletion_response = get_mixpanel_response_for_agent(
        'function main(){{return Events(params).filter(function(event){{return (event.properties.environment=="{env}"&&event.properties.agent_type=="agent1")}}).groupBy(["name"], mixpanel.reducer.count())}}',
        "agent_deleted",
        start_date,
        end_date,
    )
    logger.info("get_agent_data_mixpanel finished.")
    return {
        "new_agent3_count": agent_3_response[0]["value"] if agent_3_response else 0,
        "new_agent_3_converted_agent1": (
            agent_3_agent1_conversion_response[0]["value"]
            if agent_3_agent1_conversion_response
            else 0
        ),
        "new_agent_2_converted_agent1": (
            agent_2_agent1_conversion_response[0]["value"]
            if agent_2_agent1_conversion_response
            else 0
        ),
        "new_agent_4_converted_agent1": (
            agent_4_agent1_conversion_response[0]["value"]
            if agent_4_agent1_conversion_response
            else 0
        ),
        "new_agent4_count": agent_4_response[0]["value"] if agent_4_response else 0,
        "agent1_deleted_count": (
            agent_1_deletion_response[0]["value"] if agent_1_deletion_response else 0
        ),
    }


def get_mixpanel_response_for_agent(script, key_name, start_date, end_date):
    agent_script = script.format(env=settings.APP_ENVIRONMENT)
    agent_payload = create_mixpanel_payload(
        (MIXPANEL_EVENT_MESSAGES[key_name],), start_date, end_date, agent_script
    )
    return send_mix_panel_request(agent_payload)


@app.task
def send_report_email(report_data, date):
    from templated_email import send_templated_mail as _send_templated_mail

    logger.info(f"sending report data to {', '.join(REPORT_RECIPIENTS)}")

    _send_templated_mail(
        template_name="daily_report.html",
        from_email="AgentLoop<connect@agentloop.us>",
        recipient_list=REPORT_RECIPIENTS,
        context={"report_data": report_data, "date": date},
        cc=None,
        bcc=settings.EMAIL_BCC,
        fail_silently=False,
        connection=None,
        headers=None,
        template_prefix=None,
        template_suffix=None,
        create_link=None,
    )


@app.task
def send_report_email_v2(report_data, date):
    from templated_email import send_templated_mail as _send_templated_mail

    recipients = ("udit.jain@opscale.io",)

    logger.info(f"sending report data to {', '.join(recipients)}")

    _send_templated_mail(
        template_name="daily_report.html",
        from_email="AgentLoop<connect@agentloop.us>",
        recipient_list=recipients,
        context={"report_data": report_data, "date": date},
        cc=None,
        bcc=settings.EMAIL_BCC,
        fail_silently=False,
        connection=None,
        headers=None,
        template_prefix=None,
        template_suffix=None,
        create_link=None,
    )


@app.task
def create_daily_statistics_report():
    logger.info("create_daily_statistics_report function triggered")

    now = datetime.now(timezone.utc)
    now_date = now.date()
    yesterday = now - timedelta(days=1)
    yesterday_date = yesterday.date()
    last_week = now - timedelta(weeks=1)
    last_week_date = last_week.date()

    all_agents = ApplicationUser.objects.all()
    all_houses = House.objects.all()
    android_app_payments = AndroidPaymentHistory.objects.all()
    ios_app_payments = IOSPaymentHistory.objects.all()
    listhub_listings = all_houses.filter(
        listing_type=House.LISTING_TYPES.listhublisting
    )
    amazing_properties = all_houses.filter(
        listing_type=House.LISTING_TYPES.amazinglisting
    )
    sneak_peaks = all_houses.filter(listing_type=House.LISTING_TYPES.minutelisting)

    agent1s = all_agents.filter(agent_type=ApplicationUser.AGENT_TYPE_CHOICES.agent1)

    agent1_count = agent1s.count()
    yesterdays_agent1_count_data = AgentCount.objects.filter(
        created__date=yesterday_date,
        agent_type=ApplicationUser.AGENT_TYPE_CHOICES.agent1,
    ).order_by("-created")
    if (
        yesterdays_agent1_count_data.count() == 0
    ):  # when we do not have any rows for the table
        yesterdays_agent1_count = agent1_count
    else:
        yesterdays_agent1_count = yesterdays_agent1_count_data.first().count
    weekly_agent1_count_data = AgentCount.objects.filter(
        created__date__lt=now_date,
        created__date__gte=last_week_date,
        agent_type=ApplicationUser.AGENT_TYPE_CHOICES.agent1,
    ).order_by("created")
    if weekly_agent1_count_data.count() == 0:
        week_start_agent1_count = agent1_count
    else:
        week_start_agent1_count = weekly_agent1_count_data.first().count
    todays_agent1_count_data = AgentCount.objects.create(
        count=agent1_count, agent_type=ApplicationUser.AGENT_TYPE_CHOICES.agent1
    )
    new_agent1_count_24hrs = todays_agent1_count_data.count - yesterdays_agent1_count
    new_agent1_count_1week = todays_agent1_count_data.count - week_start_agent1_count

    new_listings_count_24hrs = listhub_listings.filter(
        created__lte=now, created__gt=yesterday
    ).count()
    new_listings_count_1week = listhub_listings.filter(
        created__lte=now, created__gt=last_week
    ).count()
    new_amazing_property_count_24hrs = amazing_properties.filter(
        created__lte=now, created__gt=yesterday
    ).count()
    new_amazing_property_count_1week = amazing_properties.filter(
        created__lte=now, created__gt=last_week
    ).count()
    new_sneak_peaks_count_24hrs = sneak_peaks.filter(
        created__lte=now, created__gt=yesterday
    ).count()
    new_sneak_peaks_count_1week = sneak_peaks.filter(
        created__lte=now, created__gt=last_week
    ).count()

    revenue_amount_24hrs = (
        android_app_payments.filter(created__lte=now, created__gt=yesterday).count()
        + ios_app_payments.filter(created__lte=now, created__gt=yesterday).count()
    )
    revenue_amount_1week = (
        android_app_payments.filter(created__lte=now, created__gt=last_week).count()
        + ios_app_payments.filter(created__lte=now, created__gt=last_week).count()
    )
    app_purchase_amount = 4.99

    logger.info("Database query done")

    daily_metrics = {
        "new_connection_request_receiver": 0,
        "new_connection_request_sender": 0,
        "connection_request_accept": 0,
        "property_interest": 0,
        "property_not_interested": 0,
        "new_self_listing_notification": 0,
    }

    weekly_metrics = {
        "new_connection_request_receiver": 0,
        "new_connection_request_sender": 0,
        "connection_request_accept": 0,
        "property_interest": 0,
        "property_not_interested": 0,
        "new_self_listing_notification": 0,
    }

    data_24hrs = get_mixpanel_data(yesterday_date, yesterday_date)
    data_1week = get_mixpanel_data(last_week_date, yesterday_date)

    if data_24hrs:
        for event_data in data_24hrs:
            key_name = REVERSE_MIXPANEL_EVENT_MESSAGES[event_data["key"][0]]
            daily_metrics[key_name] = event_data["value"]

    if data_1week:
        for event_data in data_1week:
            key_name = REVERSE_MIXPANEL_EVENT_MESSAGES[event_data["key"][0]]
            weekly_metrics[key_name] = event_data["value"]

    agents_data_mixpanel_24hrs = get_agent_data_mixpanel(yesterday_date, yesterday_date)
    agents_data_mixpanel_1week = get_agent_data_mixpanel(last_week_date, yesterday_date)

    # NOTE: TEMP fix to make sense of data as there is inconsistency in data from DB and from Mixpanel Events.
    new_agent1_count_24hrs = (
        agents_data_mixpanel_24hrs["new_agent_3_converted_agent1"]
        + agents_data_mixpanel_24hrs["new_agent_2_converted_agent1"]
        + agents_data_mixpanel_24hrs["new_agent_4_converted_agent1"]
        - agents_data_mixpanel_24hrs["agent1_deleted_count"]
    )
    new_agent1_count_1week = (
        agents_data_mixpanel_1week["new_agent_3_converted_agent1"]
        + agents_data_mixpanel_1week["new_agent_2_converted_agent1"]
        + agents_data_mixpanel_1week["new_agent_4_converted_agent1"]
        - agents_data_mixpanel_1week["agent1_deleted_count"]
    )

    logger.info("Generating report data")

    report_data = {
        # 'agent1_count': {'label': 'Total Agent1 accounts', 'value': agent1_count},
        "new_agent1_count_24hrs": {
            "label": "New Agent1 accounts in the past 24hrs",
            "value": new_agent1_count_24hrs,
        },
        "new_agent1_count_1week": {
            "label": "New Agent1 accounts in the past week",
            "value": new_agent1_count_1week,
        },
        "new_agent3_count_24hrs": {
            "label": "New Agent3 accounts in the past 24hrs",
            "value": agents_data_mixpanel_24hrs["new_agent3_count"],
        },
        "new_agent3_count_1week": {
            "label": "New Agent3 accounts in the past week",
            "value": agents_data_mixpanel_1week["new_agent3_count"],
        },
        "new_agent3_verified_count_24hrs": {
            "label": "New Agent3 accounts that coverted to agent1 in the past 24hrs",
            "value": agents_data_mixpanel_24hrs["new_agent_3_converted_agent1"],
        },
        "new_agent3_verified_count_1week": {
            "label": "New Agent3 accounts that coverted to agent1 in the past week",
            "value": agents_data_mixpanel_1week["new_agent_3_converted_agent1"],
        },
        "new_agent2_verified_count_24hrs": {
            "label": "New Agent2 accounts that coverted to agent1 in the past 24hrs",
            "value": agents_data_mixpanel_24hrs["new_agent_2_converted_agent1"],
        },
        "new_agent2_verified_count_1week": {
            "label": "New Agent2 accounts that coverted to agent1 in the past week",
            "value": agents_data_mixpanel_1week["new_agent_2_converted_agent1"],
        },
        "new_agent4_verified_count_24hrs": {
            "label": "New Agent4 accounts that coverted to agent1 in the past 24hrs",
            "value": agents_data_mixpanel_24hrs["new_agent_4_converted_agent1"],
        },
        "new_agent4_verified_count_1week": {
            "label": "New Agent4 accounts that coverted to agent1 in the past week",
            "value": agents_data_mixpanel_1week["new_agent_4_converted_agent1"],
        },
        "agent1_deleted_count_24hrs": {
            "label": "Agent1 accounts that were deleted in the past 24hrs",
            "value": agents_data_mixpanel_24hrs["agent1_deleted_count"],
        },
        "agent1_deleted_count_1week": {
            "label": "Agent1 accounts that were deleted in the past week",
            "value": agents_data_mixpanel_1week["agent1_deleted_count"],
        },
        "new_agent4_count_24hrs": {
            "label": "New Agent4 accounts in the past 24hrs",
            "value": agents_data_mixpanel_24hrs["new_agent4_count"],
        },
        "new_agent4_count_1week": {
            "label": "New Agent4 accounts in the past week",
            "value": agents_data_mixpanel_1week["new_agent4_count"],
        },
        "new_senders_of_connection_request_24hrs": {
            "label": "New users who have sent connection requests in the past 24hrs",
            "value": daily_metrics["new_connection_request_sender"],
        },
        "new_senders_of_connection_request_1week": {
            "label": "New users who have sent connection requests in the past week",
            "value": weekly_metrics["new_connection_request_sender"],
        },
        "new_connection_request_receiver_24hrs": {
            "label": "New users who have received connection requests in the past 24hrs",
            "value": daily_metrics["new_connection_request_receiver"],
        },
        "new_connection_request_receiver_1week": {
            "label": "New users who have received connection requests in the past week",
            "value": weekly_metrics["new_connection_request_receiver"],
        },
        "connection_request_accept_24hrs": {
            "label": "New connection acceptances in the past 24hrs",
            "value": daily_metrics["connection_request_accept"],
        },
        "connection_request_accept_1week": {
            "label": "New connection acceptances in the past week",
            "value": weekly_metrics["connection_request_accept"],
        },
        "new_listings_count_24hrs": {
            "label": "New Listings in the past 24hrs",
            "value": new_listings_count_24hrs,
        },
        "new_listings_count_1week": {
            "label": "New Listings in the past week",
            "value": new_listings_count_1week,
        },
        "new_amazing_property_count_24hrs": {
            "label": "New Amazing Property in the past 24hrs",
            "value": new_amazing_property_count_24hrs,
        },
        "new_amazing_property_count_1week": {
            "label": "New Amazing Property in the past week",
            "value": new_amazing_property_count_1week,
        },
        "new_sneak_peaks_count_24hrs": {
            "label": "New Sneak Peaks in the past 24hrs",
            "value": new_sneak_peaks_count_24hrs,
        },
        "new_sneak_peaks_count_1week": {
            "label": "New Sneak Peaks in the past week",
            "value": new_sneak_peaks_count_1week,
        },
        "revenue_amount_24hrs": {
            "label": "Revenue in the past 24hrs",
            "value": f"USD {revenue_amount_24hrs * app_purchase_amount}",
        },
        "revenue_amount_1week": {
            "label": "Revenue in the past week",
            "value": f"USD {revenue_amount_1week * app_purchase_amount}",
        },
        "property_interest_24hrs": {
            "label": "Property Interests Swipes in the past 24hrs",
            "value": daily_metrics["property_interest"],
        },
        "property_interest_1week": {
            "label": "Property Interests Swipes in the past week",
            "value": weekly_metrics["property_interest"],
        },
        "property_not_interested_24hrs": {
            "label": "Not Interested Swipes in the past 24hrs",
            "value": daily_metrics["property_not_interested"],
        },
        "property_not_interested_1week": {
            "label": "Not Interested Swipes in the past week",
            "value": weekly_metrics["property_not_interested"],
        },
        "new_self_listing_notification_24hrs": {
            "label": "Agent1 that received push notifications for their new MLS listing in the past 24hrs",
            "value": daily_metrics["new_self_listing_notification"],
        },
        "new_self_listing_notification_1week": {
            "label": "Agent1 that received push notifications for their new MLS listing in the past week",
            "value": weekly_metrics["new_self_listing_notification"],
        },
    }

    logger.info("Report data generated")

    send_report_email.apply_async(
        (report_data, now_date), eta=(now + timedelta(hours=8))
    )  # send report after 8 hours of task start (8pm UTC)


def daily_it(start, finish):
    while finish > start:
        old_start = start
        start = start + timedelta(days=1)
        yield old_start


@app.task(soft_time_limit=36000, time_limit=43200)  # 10 hours to 12 hours
def create_30_day_statistics_report():
    logger.info("create_monthly_statistics_report function triggered")

    now = datetime.now(timezone.utc)
    now_date = now.date()
    past = now - timedelta(days=30)
    past_date = past.date()

    all_houses = House.objects.all()
    android_app_payments = AndroidPaymentHistory.objects.all()
    ios_app_payments = IOSPaymentHistory.objects.all()
    listhub_listings = all_houses.filter(
        listing_type=House.LISTING_TYPES.listhublisting
    )
    amazing_properties = all_houses.filter(
        listing_type=House.LISTING_TYPES.amazinglisting
    )
    sneak_peaks = all_houses.filter(listing_type=House.LISTING_TYPES.minutelisting)

    app_purchase_amount = 4.99

    time.sleep(900)  # offset 15 minutes for daily report task

    with tempfile.NamedTemporaryFile(mode="r+") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=[
                "date",
                # 'agent1_count', 'new_agent1_count',
                "new_agent3_count",
                "new_agent4_count",
                "new_agent3_converted_agent1_count",
                "new_agent2_converted_agent1_count",
                "new_agent4_converted_agent1_count",
                "agent1_deleted_count",
                "connection_request_sender_count",
                "connection_request_receiver_count",
                "connection_request_accepted_count",
                "new_listings_count",
                "new_amazing_property_count",
                "new_sneakpeak_count",
                "property_interested_count",
                "property_not_interested_count",
                "new_self_listings_count",
                "revenue_amount",
            ],
        )

        writer.writeheader()

        logger.info("Generating report data")

        for current_datetime in daily_it(past, now):
            current_date = current_datetime.date()

            # current agent count would already be created by daily report task
            # agent count for current date is created by daily report after the date is changed at midnight
            current_agent1_count = AgentCount.objects.filter(
                created__date=(current_date + timedelta(days=1)),
                agent_type=ApplicationUser.AGENT_TYPE_CHOICES.agent1,
            ).order_by("-created")
            if (
                current_agent1_count.count() == 0
            ):  # when we do not have any rows for the table
                current_agent1_count_value = "N\A"
            else:
                current_agent1_count_value = current_agent1_count.first().count

            yesterdays_agent1_count = AgentCount.objects.filter(
                created__date=current_date,
                agent_type=ApplicationUser.AGENT_TYPE_CHOICES.agent1,
            ).order_by("-created")
            if (
                yesterdays_agent1_count.count() == 0
            ):  # when we do not have any rows for the table
                yesterdays_agent1_count_value = "N\A"
            else:
                yesterdays_agent1_count_value = yesterdays_agent1_count.first().count

            new_agent1_count = (
                "N\A"
                if (
                    current_agent1_count_value == "N\A"
                    or yesterdays_agent1_count_value == "N\A"
                )
                else current_agent1_count_value - yesterdays_agent1_count_value
            )

            new_listings_count = listhub_listings.filter(
                created__date=current_date
            ).count()
            new_amazing_property_count = amazing_properties.filter(
                created__date=current_date
            ).count()
            new_sneak_peaks_count = sneak_peaks.filter(
                created__date=current_date
            ).count()

            revenue_amount = (
                android_app_payments.filter(created__date=current_date).count()
                + ios_app_payments.filter(created__date=current_date).count()
            )

            metrics = {
                "new_connection_request_receiver": 0,
                "new_connection_request_sender": 0,
                "connection_request_accept": 0,
                "property_interest": 0,
                "property_not_interested": 0,
                "new_self_listing_notification": 0,
            }

            if mixpanel_data := get_mixpanel_data(
                current_date, current_date
            ):  # 1 requests are done here
                for event_data in mixpanel_data:
                    key_name = REVERSE_MIXPANEL_EVENT_MESSAGES[event_data["key"][0]]
                    metrics[key_name] = event_data["value"]

            agents_data_mixpanel = get_agent_data_mixpanel(
                current_date, current_date
            )  # 6 requests are done here

            writer.writerow(
                {
                    "date": current_date,
                    # 'agent1_count': current_agent1_count_value, 'new_agent1_count': new_agent1_count,
                    "new_agent3_count": agents_data_mixpanel["new_agent3_count"],
                    "new_agent4_count": agents_data_mixpanel["new_agent4_count"],
                    "new_agent3_converted_agent1_count": agents_data_mixpanel[
                        "new_agent_3_converted_agent1"
                    ],
                    "new_agent2_converted_agent1_count": agents_data_mixpanel[
                        "new_agent_2_converted_agent1"
                    ],
                    "new_agent4_converted_agent1_count": agents_data_mixpanel[
                        "new_agent_4_converted_agent1"
                    ],
                    "agent1_deleted_count": agents_data_mixpanel[
                        "agent1_deleted_count"
                    ],
                    "connection_request_sender_count": metrics[
                        "new_connection_request_sender"
                    ],
                    "connection_request_receiver_count": metrics[
                        "new_connection_request_receiver"
                    ],
                    "connection_request_accepted_count": metrics[
                        "connection_request_accept"
                    ],
                    "new_listings_count": new_listings_count,
                    "new_amazing_property_count": new_amazing_property_count,
                    "new_sneakpeak_count": new_sneak_peaks_count,
                    "property_interested_count": metrics["property_interest"],
                    "property_not_interested_count": metrics["property_not_interested"],
                    "new_self_listings_count": metrics["new_self_listing_notification"],
                    "revenue_amount": f"USD {revenue_amount * app_purchase_amount}",
                }
            )

            time.sleep(525)  # rate limit is 60 requests for an hour so 8.75 minutes

        logger.info("Report data wrote to CSV, Sending Mail...")

        csvfile.seek(0)

        mail = EmailMessage(
            "Monthly Data Report",
            f"Timeline: {past_date} -> {now_date - timedelta(days=1)}. The details of the report are attached as a CSV file.",
            "AgentLoop<connect@agentloop.us>",
            REPORT_RECIPIENTS,
        )
        mail.attach(
            f"{past_date}_{now_date - timedelta(days=1)}_Monthly_Report",
            csvfile.read(),
            "text/csv",
        )
        mail.send()

        logger.info("Mail Sent")
