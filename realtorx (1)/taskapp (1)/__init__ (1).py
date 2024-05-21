import os

from django.conf import settings

from celery import Celery
from celery.schedules import crontab

if not settings.configured:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

app = Celery("realtorx")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.set_default()
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.beat_schedule = {
    "realtorx.custom_auth.tasks.send_email_with_in_coming_following_requests": {
        "task": "realtorx.custom_auth.tasks.send_email_with_in_coming_following_requests",
        "schedule": crontab(minute=0, hour=16, day_of_week="tue"),
        "args": (),
    },
    "realtorx.custom_auth.tasks.send_email_with_list_hub_in_coming_following_requests": {
        "task": "realtorx.custom_auth.tasks.send_email_with_list_hub_in_coming_following_requests",
        "schedule": crontab(minute=0, hour=16, day_of_week="wed"),
        "args": (),
    },
    "realtorx.custom_auth.tasks.send_email_to_agent2_regarding_daily_interest_activity_of_new_listing": {
        "task": "realtorx.custom_auth.tasks.send_email_to_agent2_regarding_daily_interest_activity_of_new_listing",
        "schedule": crontab(minute=0, hour=16),
        "args": (),
    },
    "realtorx.custom_auth.tasks.send_email_to_agent3_regarding_daily_interest_activity_of_new_listing": {
        "task": "realtorx.custom_auth.tasks.send_email_to_agent3_regarding_daily_interest_activity_of_new_listing",
        "schedule": crontab(minute=0, hour=16),
        "args": (),
    },
    "realtorx.houses.tasks.daily_interest_agent_notification": {
        "task": "realtorx.houses.tasks.daily_interest_agent_notification",
        "schedule": crontab(minute=0, hour=16, day_of_week="mon-sat"),
        "args": (),
    },
    # 'realtorx.houses.tasks.daily_interest_seller_landlord_notification': {
    #     'task': 'realtorx.houses.tasks.daily_interest_seller_landlord_notification',
    #     'schedule': crontab(minute=0, hour=16, day_of_week='mon-sat'),
    #     'args': (),
    # },
    # Comment out the below cron function to disable the listhub data pull.
    # In order to create new properties and update the existing properties based on the ListHub data.
    # We have trigged the below get_list_hub_data cron at every 30 minutes.
    "realtorx.crm.views.get_list_hub_data": {
        "task": "realtorx.crm.views.get_list_hub_data",
        "schedule": crontab(minute=0, hour="7"),
        "args": (),
    },
    "realtorx.registrations.tasks.delete_trial_user": {
        "task": "realtorx.registrations.tasks.delete_trial_user",
        "schedule": crontab(minute=0, hour=4),
        "args": (),
    },
    "realtorx.houses.tasks.daily_check_amazing_listing": {
        "task": "realtorx.houses.tasks.daily_check_amazing_listing",
        "schedule": crontab(minute=0, hour=4),
        "args": (),
    },
    # 'realtorx.custom_auth.tasks.send_email_with_in_coming_following_requests_without_password': {
    #     'task': 'realtorx.custom_auth.tasks.send_email_with_in_coming_following_requests_without_password',
    #     'schedule': crontab(minute=0, hour=16),
    #     'args': (),
    # },
    "realtorx.crm.tasks.ftp_upload": {
        "task": "realtorx.crm.tasks.ftp_upload",
        "schedule": crontab(minute=0, hour=4),
        "args": (),
    },
    # Disabling the tasks for listhub api
    # 'realtorx.crm.tasks.fetch_listhub_listings_v3': {
    #     'task': 'realtorx.crm.tasks.fetch_listhub_listings_v3',
    #     'schedule': timedelta(seconds=30),
    #     'args': (),
    # },
    # 'realtorx.crm.tasks.fetch_listhub_listings_daily': {
    #     'task': 'realtorx.crm.tasks.fetch_listhub_listings_daily',
    #     'schedule': crontab(minute=0, hour=0),
    #     'args': (),
    # },
    # 'realtorx.statistics.tasks.send_mixpanel_event': {
    #     'task': 'realtorx.statistics.tasks.send_mixpanel_event',
    #     'schedule': crontab(minute=0, hour=0),
    #     'args': (),
    # },
    "realtorx.statistics.tasks.create_daily_statistics_report": {
        "task": "realtorx.statistics.tasks.create_daily_statistics_report",
        "schedule": crontab(minute=0, hour=0),
        "args": (),
    },
    "realtorx.statistics.tasks.get_email_type_report": {
        "task": "realtorx.statistics.tasks.get_email_type_report",
        "schedule": crontab(minute=0, hour=2),
        "args": (),
    },
}

app.conf.timezone = "UTC"
