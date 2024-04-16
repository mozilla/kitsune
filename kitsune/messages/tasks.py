import logging

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.db import transaction
from django.urls import reverse
from django.utils.translation import gettext as _

from celery import shared_task

from kitsune.messages.models import InboxMessage, OutboxMessage
from kitsune.messages.signals import message_sent
from kitsune.sumo.email_utils import make_mail, safe_translation, send_messages
from kitsune.users.models import Setting

log = logging.getLogger("k.task")


@shared_task
def email_private_message(inbox_message_id):
    """Send notification of a new private message."""
    inbox_message = InboxMessage.objects.get(id=inbox_message_id)
    log.debug("Sending email for user (%s)" % (inbox_message.to,))

    user = inbox_message.to

    @safe_translation
    def _send_mail(locale):
        # Avoid circular import issues
        from kitsune.users.templatetags.jinja_helpers import display_name

        subject = _("[SUMO] You have a new private message from [{sender}]")
        subject = subject.format(sender=display_name(inbox_message.sender))

        msg_url = reverse("messages.read", kwargs={"msgid": inbox_message.id})
        settings_url = reverse("users.edit_settings")

        from kitsune.sumo.templatetags.jinja_helpers import add_utm

        context = {
            "sender": inbox_message.sender,
            "message": inbox_message.message,
            "message_html": inbox_message.content_parsed,
            "message_url": add_utm(msg_url, "messages-new"),
            "unsubscribe_url": add_utm(settings_url, "messages-new"),
            "host": Site.objects.get_current().domain,
        }

        mail = make_mail(
            subject=subject,
            text_template="messages/email/private_message.ltxt",
            html_template="messages/email/private_message.html",
            context_vars=context,
            from_email=settings.TIDINGS_FROM_ADDRESS,
            to_email=inbox_message.to.email,
        )

        send_messages([mail])

    if hasattr(user, "profile"):
        locale = user.profile.locale
    else:
        locale = settings.WIKI_DEFAULT_LANGUAGE

    _send_mail(locale)


@shared_task
def send_message(to, text=None, sender=None):
    """Send a private message.

    :arg to: Users or Groups to send the message to
    :arg sender: the User who is sending the message
    :arg text: the message text
    """

    # We need a sender, a message, and someone to send it to
    if not sender or not text or not to:
        return
    # Collect users and groups directly without using set comprehensions in loops
    users = set()
    groups = set()
    for recipient in to:
        if isinstance(recipient, User):
            users.add(recipient)
        elif isinstance(recipient, Group):
            groups.add(recipient)
    # This is all the users that are going to receive the message
    receivers = users | set(User.objects.filter(groups__in=groups).distinct())

    with transaction.atomic():
        outbox_message = OutboxMessage.objects.create(sender=sender, message=text)
        # Add the users from the To field to the outbox message, not all the users
        # that are going to receive the message - this way we don't overwhelm the
        # message UI
        outbox_message.to.set(users)

        if groups:
            # Add the groups from the To field to the message
            outbox_message.to_group.set(groups)

        set_of_user_pks_to_email_private_message = set(
            Setting.objects.filter(
                user__in=receivers, name="email_private_messages", value=True
            ).values_list("user__pk", flat=True)
        )

        for recipient in receivers:
            inbox_message = InboxMessage.objects.create(sender=sender, to=recipient, message=text)
            # If we had a user, and we made them an inbox message,
            # we should also add the groups to their message as well
            if groups:
                inbox_message.to_group.set(groups)
            if recipient.pk in set_of_user_pks_to_email_private_message:
                email_private_message(inbox_message_id=inbox_message.id)

        message_sent.send(sender=InboxMessage, to=to, text=text, msg_sender=sender)
