from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db.models import Q
from kitsune.messages.models import InboxMessage, OutboxMessage
from kitsune.messages.signals import message_sent
from kitsune.messages.tasks import email_private_message
from kitsune.sumo.utils import webpack_static
from kitsune.users.models import Setting
from kitsune.users.templatetags.jinja_helpers import profile_avatar


def send_message(to, text=None, sender=None):
    """Send a private message.
    :arg to: A dictionary with two keys, 'users' and 'groups',
            each containing a list usernames or group names.
    """

    # We need a sender, a message, and someone to send it to
    if not sender or not text or not to:
        return

    # Resolve all unique user ids, including those in groups
    # We need to keep group users separate for email notifications

    to_users = to.get("users", [])
    to_groups = to.get("groups", [])

    users = User.objects.filter(username__in=to_users)
    groups = Group.objects.filter(name__in=to_groups, profile__isnull=False)

    all_recipients_of_message = set(users.values_list("id", flat=True)) | set(
        User.objects.filter(groups__in=groups).values_list("id", flat=True)
    )

    # Create the outbox message
    outbox_message = OutboxMessage.objects.create(sender=sender, message=text)
    outbox_message.to.set(users)
    outbox_message.to_group.set(groups)

    # Fetch settings for email notifications in one go
    # For now, we only send emails to users who were individually
    # listed in 'to' field, not to users who are from groups
    users_to_email = set(
        Setting.objects.filter(
            user__in=users, name="email_private_messages", value=True
        ).values_list("user__id", flat=True)
    )

    # Create inbox messages and handle emails
    inbox_messages = [
        InboxMessage(sender=sender, to_id=user_id, message=text)
        for user_id in all_recipients_of_message
    ]

    recipient_id_to_message_id = {
        msg.to_id: msg.id for msg in InboxMessage.objects.bulk_create(inbox_messages)
    }

    # Assuming messages are fetched again with IDs if necessary
    for user_id in users_to_email:
        if message_id := recipient_id_to_message_id.get(user_id):
            email_private_message.delay(inbox_message_id=message_id)

    # Send a signal if needed
    message_sent.send(sender=InboxMessage, to=to, text=text, msg_sender=sender)


def unread_count_for(user):
    """Returns the number of unread messages for the specified user."""
    return InboxMessage.objects.filter(to=user, read=False).count()


def create_suggestion(item):
    """Create a dictionary object for the autocomplete suggestion."""
    is_user = isinstance(item, User)
    return {
        "type": "User" if is_user else "Group",
        "type_icon": webpack_static(
            settings.DEFAULT_USER_ICON if is_user else settings.DEFAULT_GROUP_ICON
        ),
        "name": item.username if is_user else item.name,
        "type_and_name": f"User: {item.username}" if is_user else f"Group: {item.name}",
        "display_name": item.profile.name if is_user else item.name,
        "avatar": (
            profile_avatar(item, 24) if is_user else webpack_static(settings.DEFAULT_AVATAR)
        ),
    }


def find_users_and_groups_by_search(pre, show_groups=False, exact=False):
    """Given a name or start of a name, return a list of users and groups."""
    if exact:
        user_criteria = Q(username=pre) | Q(profile__name=pre)
        group_criteria = Q(name=pre)
    else:
        user_criteria = Q(username__istartswith=pre) | Q(profile__name__istartswith=pre)
        group_criteria = Q(name__istartswith=pre)

    users = User.objects.filter(
        user_criteria, is_active=True, profile__is_fxa_migrated=True
    ).select_related("profile")[:10]

    if show_groups:
        groups = Group.objects.filter(group_criteria, profile__isnull=False)[:10]

    user_list = list(users)

    return user_list + list(groups) if show_groups else user_list
