from realtorx.following.models import ConnectionsGroup


def create_groups(instance):
    if (
        instance.sender.agency == instance.recipient.agency
        and instance.sender.full_name != ""
        and instance.recipient.full_name != ""
    ):
        if not instance.sender.agency or not instance.recipient.agency:
            return
        sender_group, created = ConnectionsGroup.objects.update_or_create(
            owner=instance.sender,
            name=instance.sender.agency.name,
        )
        sender_group.members.add(instance.recipient)

        recipient_group, created = ConnectionsGroup.objects.update_or_create(
            owner=instance.recipient,
            name=instance.recipient.agency.name,
        )
        recipient_group.members.add(instance.sender)

    if (
        instance.sender.brokerage_phone_number
        and instance.sender.agency
        and instance.sender.full_name != ""
        and instance.recipient.full_name != ""
    ):
        if (
            instance.sender.brokerage_phone_number
            == instance.recipient.brokerage_phone_number
            and instance.sender.agency == instance.recipient.agency
        ):
            if (not instance.sender.agency or not instance.recipient.agency) and (
                not instance.sender.brokerage_phone_number
                or not instance.recipient.brokerage_phone_number
            ):
                return
            sender_group, created = ConnectionsGroup.objects.update_or_create(
                owner=instance.sender,
                name=instance.sender.agency.name + " - Internal Office",
            )
            sender_group.members.add(instance.recipient)

            recipient_group, created = ConnectionsGroup.objects.update_or_create(
                owner=instance.recipient,
                name=instance.sender.agency.name + " - Internal Office",
            )
            recipient_group.members.add(instance.sender)
