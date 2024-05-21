import operator
from functools import reduce
from realtorx.following.models import FollowingRequest
from realtorx.taskapp import app
from realtorx.custom_auth.models import ApplicationUser
from django.db.models import Q
from fcm_django.models import FCMDevice
from firebase_admin import messaging
import datetime
import pytz
from realtorx.utils.firebase.app import Firebase
from realtorx.utils.mixpanel import track_mixpanel_event
from realtorx.custom_auth.tasks import (
    send_connection_request_email_to_agent2,
    send_connection_request_email_to_agent3,
    send_follow_request,
)


def send_to_push(registration_tokens, title, msg):
    aps = messaging.Aps(sound="default", badge=0)
    payload = messaging.APNSPayload(aps)
    while len(registration_tokens) > 0:
        device_tokens = registration_tokens[:499]
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=msg),
            data={
                "push_type": "new_following_request",
            },
            apns=messaging.APNSConfig(payload=payload),
            tokens=device_tokens,
        )
        response = messaging.send_multicast(message)
        print("Success Count", response.success_count)
        failed_tokens = []
        if response.failure_count > 0:
            responses = response.responses
            for idx, resp in enumerate(responses):
                if not resp.success:
                    failed_tokens.append(registration_tokens[idx])
            print("List of tokens that caused failures: {0}".format(failed_tokens))
        del registration_tokens[:499]


def get_miunte(current_time, start_time):
    print(
        "printing current time hour and start time hour",
        current_time.hour,
        start_time.hour,
    )
    if current_time.hour > start_time.hour:
        hours = current_time.hour - start_time.hour
        print("Inside first if", hours)
        if hours > 0:
            minutes = current_time.minute + (hours * 60)
            print("Hours is less than 0", current_time.minute, hours * 60, minutes)
            return minutes + 1
    elif current_time.hour == 0 or current_time.hour == 1:
        full_time = datetime.time(0, 0, 0)
        print("Inside else if ", full_time)
        hours = current_time.hour - full_time.hour
        print("hours inside else if", current_time.hour, full_time.hour, hours)
        minutes = ((hours + 2) * 60) + current_time.minute
        print(
            "minutes inside else if",
            hours + 2,
            ((hours + 2) * 60),
            current_time.minute,
            minutes,
        )
        return minutes + 1
    else:
        print("Inside else ", current_time.minute)
        return current_time.minute + 1


def getting_users(group_no):
    phone_device_token_list = list(
        set(
            FollowingRequest.objects.filter(
                status="pending", recipient__group_number=group_no
            ).values_list("recipient", flat=True)
        )
    )
    registration_tokens = list(
        FCMDevice.objects.filter(
            user_id__in=phone_device_token_list, active=True
        ).values_list("registration_id", flat=True)
    )
    print(
        "-------> phone_device_token_list",
        phone_device_token_list,
        len(phone_device_token_list),
    )
    print("-------> registration_tokens", registration_tokens, len(registration_tokens))
    send_to_push(
        registration_tokens,
        title="New connection request",
        msg="You have new connection requests",
    )


def send_reminder_push():
    print("call")
    print(datetime.datetime.now())
    Firebase.get_app()
    ten_am_est_to_utc = datetime.time(14, 0, 0)
    two_pm_est_to_utc = datetime.time(18, 0, 0)
    six_pm_est_to_utc = datetime.time(22, 0, 0)
    two_am_est_to_utc = datetime.time(2, 0, 0)
    now = datetime.datetime.now()
    print(ten_am_est_to_utc)
    print(two_pm_est_to_utc)
    print(six_pm_est_to_utc)
    print(two_am_est_to_utc)
    print(now.time())
    print(ten_am_est_to_utc <= now.time() < two_pm_est_to_utc)
    track_mixpanel_event(
        "AgentLoop_ADMIN",
        "connection_push_notification_track",
        {"time": str(now.time()), "type": "send_reminder_push_called"},
    )

    if ten_am_est_to_utc <= now.time() < two_pm_est_to_utc:
        print("Inside ten_am_est_to_utc")
        group_no = get_miunte(now, ten_am_est_to_utc)
        print("Group Number", group_no)
        getting_users(group_no)
        print("success")
        track_mixpanel_event(
            "AgentLoop_ADMIN",
            "connection_push_notification_track",
            {
                "time": str(now.time()),
                "group_no": str(group_no),
                "type": "ten_am_est_to_utc",
            },
        )
    elif two_pm_est_to_utc <= now.time() < six_pm_est_to_utc:
        print("Inside two_pm_est_to_utc")
        group_no = get_miunte(now, two_pm_est_to_utc)
        print("Group Number", group_no)
        getting_users(group_no)
        print("success")
        track_mixpanel_event(
            "AgentLoop_ADMIN",
            "connection_push_notification_track",
            {
                "time": str(now.time()),
                "group_no": str(group_no),
                "type": "two_pm_est_to_utc",
            },
        )
    elif now.time() >= six_pm_est_to_utc:
        print("Inside six_pm_est_to_utc greater equal")
        group_no = get_miunte(now, six_pm_est_to_utc)
        print("Group Number", group_no)
        getting_users(group_no)
        print("success")
        track_mixpanel_event(
            "AgentLoop_ADMIN",
            "connection_push_notification_track",
            {
                "time": str(now.time()),
                "group_no": str(group_no),
                "type": "six_pm_est_to_utc_greater_equal",
            },
        )
    elif now.time() < two_am_est_to_utc:
        print("Inside smaller two_am_est_to_utc")
        group_no = get_miunte(now, six_pm_est_to_utc)
        print("Group Number", group_no)
        getting_users(group_no)
        print("success")
        track_mixpanel_event(
            "AgentLoop_ADMIN",
            "connection_push_notification_track",
            {
                "time": str(now.time()),
                "group_no": str(group_no),
                "type": "now_time_less_than_two_am_est_to_utc",
            },
        )


@app.task
def send_connection_request_from_steves_account():
    steve = ApplicationUser.objects.get(email="steve.pharr@agentloop.us")
    agent_2_activity_threshold = datetime.datetime(2022, 3, 1, tzinfo=pytz.UTC)
    connection_request_sent_by_steve = FollowingRequest.objects.filter(
        sender=steve
    ).values_list("recipient_id", flat=True)
    connection_request_sent_to_steve = FollowingRequest.objects.filter(
        recipient=steve
    ).values_list("sender_id", flat=True)
    connection_request_to_be_sent_by_steve_to_agent1 = ApplicationUser.objects.filter(
        Q(agent_type="agent1")
        & ~Q(id__in=connection_request_sent_by_steve)
        & ~Q(id__in=connection_request_sent_to_steve)
    ).exclude(id=steve.id)
    connection_request_to_be_sent_by_steve_to_agent2 = ApplicationUser.objects.filter(
        Q(agent_type="agent2") & ~Q(id__in=connection_request_sent_by_steve)
    ).prefetch_related("houses")
    connection_request_to_be_sent_by_steve_to_agent2 = (
        connection_request_to_be_sent_by_steve_to_agent2.filter(
            Q(houses__created__gte=agent_2_activity_threshold)
            | Q(houses__modified__gte=agent_2_activity_threshold)
        ).distinct()
    )
    print(
        "---- connection_request_to_be_sent_by_steve_to_agent2",
        connection_request_to_be_sent_by_steve_to_agent2.count(),
    )
    connection_request_to_be_sent_by_steve_to_agent3 = ApplicationUser.objects.filter(
        Q(agent_type="agent3") & ~Q(id__in=connection_request_sent_by_steve)
    )
    print("connection_request_sent_by_steve", connection_request_sent_by_steve.count())
    for agent in connection_request_to_be_sent_by_steve_to_agent1[:30000]:
        process_connection_request.delay(agent.id, steve.id)
    for agent in connection_request_to_be_sent_by_steve_to_agent2[:30000]:
        process_connection_request.delay(agent.id, steve.id)
    for agent in connection_request_to_be_sent_by_steve_to_agent3[:60000]:
        process_connection_request.delay(agent.id, steve.id)


@app.task
def process_connection_request(agent_id, steves_id):
    agent = ApplicationUser.objects.get(id=agent_id)
    steve = ApplicationUser.objects.get(id=steves_id)
    if agent.agent_type == "agent2":
        print(agent.houses.count(), agent.full_name, agent.agent_type, agent.id)
        FollowingRequest.objects.create(
            sender_id=steves_id, recipient=agent, system_generated=True
        )
        send_connection_request_email_to_agent2.delay(
            steves_id, agent.id, system_generated=True
        )
    elif agent.agent_type == "agent3":
        print(agent.full_name, agent.agent_type, agent.id)
        FollowingRequest.objects.create(
            sender_id=steves_id, recipient=agent, system_generated=True
        )
        send_connection_request_email_to_agent3.delay(
            steves_id, agent.id, system_generated=True
        )
    else:
        print(agent.full_name, agent.agent_type, agent.id)
        FollowingRequest.objects.create(
            sender_id=steves_id, recipient=agent, system_generated=True
        )

    track_mixpanel_event(
        str(steve.uuid),
        "new_connection_request_receiver",
        {
            "sender_email": steve.email,
            "recipient_email": agent.email,
            "sender_uuid": str(steve.uuid),
            "recipient_uuid": str(agent.uuid),
            "sender_agent_type": steve.agent_type,
            "recipient_agent_type": agent.agent_type,
        },
    )

    track_mixpanel_event(
        str(steve.uuid),
        "new_connection_request_sender",
        {
            "sender_email": steve.email,
            "recipient_email": [agent.email],
            "sender_uuid": str(steve.uuid),
            "recipient_uuid": [str(agent.uuid)],
            "sender_agent_type": steve.agent_type,
            "recipient_agent_type": [agent.agent_type],
            "agent_1_recipient_count": 1 if agent.agent_type == "agent1" else 0,
            "agent_2_recipient_count": 1 if agent.agent_type == "agent2" else 0,
            "agent_2_recipient_skipped_count": 0,
            "agent_3_recipient_count": 1 if agent.agent_type == "agent3" else 0,
            "case": "single connection",
        },
    )


@app.task(soft_time_limit=7200, time_limit=8000)
def process_following_requests_from_phone(phone_numbers, sender_id):
    connection_requests_sent = FollowingRequest.objects.filter(
        sender__id=sender_id
    ).values_list("recipient_id", flat=True)
    connection_requests_received = FollowingRequest.objects.filter(
        recipient__id=sender_id
    ).values_list("sender_id", flat=True)

    user_ids = (
        ApplicationUser.objects.filter(
            reduce(operator.or_, (Q(phone__endswith=x) for x in phone_numbers))
            & ~Q(id__in=connection_requests_sent)
            & ~Q(id__in=connection_requests_received)
        )
        .exclude(id=sender_id)
        .exclude(full_name="")
        .distinct()
        .values_list("id", flat=True)
    )  # NOTE: If you add any changes in the logic here, also modify the logic at registrations.filters.RegistrationFilterSet

    send_follow_request.delay(list(user_ids), sender_id)
